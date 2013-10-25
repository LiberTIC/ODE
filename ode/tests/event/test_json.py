# -*- encoding: utf-8 -*-
from datetime import datetime
from unittest import TestCase

from ode.models import DBSession, Event
from ode.tests.event import TestEventMixin


def remove_id(dictionary):
    result = dict(dictionary)
    del result['id']
    return result


example_data = {
    "address": "10 rue des Roses",
    "audio_license": "CC",
    "audio_url": "http://example.com/audio",
    "author_email": "bob@example.com",
    "author_firstname": u"François",
    "author_lastname": u"Vittsjö",
    "author_telephone": "000-999-23-30",
    "country": u"日本",
    "post_code": "UVH-345",
    "description": u"""
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a
    diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula ac
    quam viverra nec consectetur ante hendrerit. Donec et mollis dolor.
    Praesent et diam eget libero egestas mattis sit amet vitae
    augue.""",
    "event_id": "abc123",
    "email": "alice@example.com",
    "firstname": "Alice",
    "language": u"Français",
    "lastname": u"Éléonore",
    "latlong": u"1.0;2.0",
    "location_name": u"Patinoire",
    "organiser": u"LiberTIC",
    "capacity": u"42",
    "price_information": u"Plutôt bon marché",
    "performers": u"Basile Dupont;José Durand",
    "photos1_license": u"License Info 1",
    "photos1_url": u"http://example.com/photo1",
    "photos2_license": u"License Info 2",
    "photos2_url": u"http://example.com/photo2",
    "press_url": u"http://example.com/photo2",
    "source_id": u"xyz123",
    "source": u"http://example.com/event-source",
    "target": u"all",
    "telephone": u"1234567890",
    "title": u"Convention des amis des éléphants",
    "town": u"上海",
    "video_license": u"Video License Info",
    "video_url": u"http://example.com/video",
    "url": u"http://example.com/events/covention-amis-elephant",
    "start_time": datetime(2013, 12, 19, 9),
    "end_time": datetime(2013, 12, 19, 9),
}
example_json = dict(example_data)
example_json['start_time'] = '2013-12-19T09:00:00'
example_json['end_time'] = '2013-12-19T09:00:00'


class TestJson(TestEventMixin, TestCase):
    maxDiff = None

    def test_root(self):
        response = self.app.get('/', status=200)
        self.assertTrue('Pyramid' in response.body)

    def post_event(self, event_info=None):
        if event_info is None:
            events_info = {'events': [{'title': u'Titre Événement'}]}
        else:
            events_info = {'events': [event_info]}
        response = self.app.post_json('/events', events_info)
        return response.json['events'][0]['id']

    def assertEqualIgnoringId(self, result, expected):
        self.assertDictEqual(remove_id(result), expected)

    def test_post_event(self):
        event_id = self.post_event()
        self.assertTitleEqual(event_id, u'Titre Événement')

    def test_post_title_too_long(self):
        very_long_title = '*' * 1001
        response = self.app.post_json('/events', {
            'title': very_long_title
        }, status=400)
        self.assertEqual(response.json['status'], 'error')

    def test_update_event(self):
        event_id = self.post_event()
        response = self.app.put_json('/events/%s' % event_id, {
            'title': 'EuroPython',
        })
        self.assertTitleEqual(event_id, 'EuroPython')
        self.assertEqual(response.json['status'], 'updated')

    def test_update_title_too_long(self):
        event_id = self.post_event()
        very_long_title = '*' * 1001
        response = self.app.put_json('/events/%s' % event_id, {
            'title': very_long_title
        }, status=400)
        self.assertEqual(response.json['status'], 'error')

    def test_list_events(self):
        self.create_event(title=u'Événement 1')
        self.create_event(title=u'Événement 2')
        response = self.app.get('/events')
        events = response.json['events']
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['title'], u'Événement 1')

    def test_get_event(self):
        id = self.post_event()
        response = self.app.get('/events/%s' % id)
        self.assertEqual(response.json['event']['title'],
                         u'Titre Événement')

    def test_delete_event(self):
        id = self.post_event()
        self.app.delete('/events/%s' % id)
        self.assertEqual(DBSession.query(Event).count(), 0)

    def test_post_all_fields(self):
        event_id = self.post_event(example_json)
        event = DBSession.query(Event).filter_by(id=event_id).first()
        self.assertEqualIgnoringId(event.to_dict(), example_data)

    def test_get_all_fields(self):
        event = self.create_event(**example_data)
        DBSession.flush()
        response = self.app.get('/events/%s' % event.id)
        self.assertEqualIgnoringId(response.json['event'], example_json)

    def test_get_invalid_id(self):
        response = self.app.get('/events/42', status=404)
        self.assertEqual(response.json['status'], 404)

    def test_put_invalid_id(self):
        response = self.app.put('/events/42', status=404)
        self.assertEqual(response.json['status'], 404)

    def test_delete_invalid_id(self):
        response = self.app.delete('/events/42', status=404)
        self.assertEqual(response.json['status'], 404)
