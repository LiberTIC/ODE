# -*- encoding: utf-8 -*-
from unittest import TestCase

from webtest import TestApp

from ode import main
from ode.tests.support import initTestingDB
from ode.models import DBSession, Event


class TestEvent(TestCase):

    def setUp(self):
        settings = {'sqlalchemy.url': 'sqlite://'}
        app = main({}, **settings)
        self.app = TestApp(app)
        initTestingDB()

    def tearDown(self):
        del self.app
        DBSession.remove()

    def test_root(self):
        response = self.app.get('/', status=200)
        self.assertTrue('Pyramid' in response.body)

    def post_event(self, event_info=None):
        if event_info is None:
            event_info = {'title': u'Titre Événement'}
        response = self.app.post_json('/events', event_info)
        return response.json['id']

    def assertTitleEqual(self, event_id, title):
        event = DBSession.query(Event).filter_by(id=event_id).first()
        self.assertEqual(event.title, title)

    def create_event(self, title):
        event = Event(title=title)
        DBSession.add(event)

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
        self.app.put_json('/events', {
            'id': event_id,
            'title': 'EuroPython',
        })
        self.assertTitleEqual(event_id, 'EuroPython')

    def test_update_title_too_long(self):
        event_id = self.post_event()
        very_long_title = '*' * 1001
        response = self.app.put_json('/events', {
            'id': event_id,
            'title': very_long_title
        }, status=400)
        self.assertEqual(response.json['status'], 'error')

    def test_list_events(self):
        self.create_event(u'Événement 1')
        self.create_event(u'Événement 2')
        response = self.app.get('/events')
        events = response.json['events']
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['title'], u'Événement 1')

    def test_get_event(self):
        id = self.post_event()
        response = self.app.get('/events/%s' % id)
        self.assertEqual(response.json['title'], u'Titre Événement')

    def test_delete_event(self):
        id = self.post_event()
        self.app.delete('/events/%s' % id)
        self.assertEqual(DBSession.query(Event).count(), 0)

    def test_post_complete_example(self):
        self.maxDiff = None
        example_data = {
            'address': '10 rue des Roses',
            'audio_license': 'CC',
            'audio_url': 'http://example.com/audio',
            'author_email': 'bob@example.com',
            'author_firstname': u'François',
            'author_lastname': u'Vittsjö',
            'author_telephone': '000-999-23-30',
            'country': u'日本',
            'post_code': 'UVH-345',
            'description': u'''
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a
            diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula ac
            quam viverra nec consectetur ante hendrerit. Donec et mollis dolor.
            Praesent et diam eget libero egestas mattis sit amet vitae
            augue.''',
            'event_id': 'abc123',
            'email': 'alice@example.com',
            'firstname': 'Alice',
            'language': u'Français',
            'lastname': u'Éléonore',
            'latlong': u"1.0;2.0",
            'location_name': u'Nîmes',
            'organiser': u'LiberTIC',
            'capacity': u'42',
            'price_information': u'Plutôt bon marché',
            'performers': u'Basile Dupont;José Durand',
            'photos1_license': u'License Info 1',
            'photos1_url': u'http://example.com/photo1',
            'photos2_license': u'License Info 2',
            'photos2_url': u'http://example.com/photo2',
            'press_url': u'http://example.com/photo2',
            'source_id': u'xyz123',
            'source': u'http://example.com/event-source',
            'target': u'all',
            'telephone': u'1234567890',
            'title': u'Convention des amis des éléphants',
            'town': u'上海',
            'video_license': u'Video License Info',
            'video_url': 'http://example.com/video',
        }
        event_id = self.post_event(example_data)
        event = DBSession.query(Event).filter_by(id=event_id).first()
        self.assertDictEqual(event.json_data(), example_data)
