from unittest import TestCase

from ode.models import DBSession, Source
from ode.tests import BaseTestMixin


class TestSource(BaseTestMixin, TestCase):

    def assertSourceCount(self, count):
        self.assertEqual(DBSession.query(Source).count(), count)

    def test_get_source(self):
        source = self.make_source()
        response = self.app.get('/v1/sources/%s' % source.id)
        self.assertEqual(response.json['source']['url'], 'http://example.com')

    def test_delete_source(self):
        source = self.make_source(producer_id=123)
        self.app.delete('/v1/sources/%s' % source.id,
                        headers={'X-ODE-Producer-Id': '123'})
        self.assertSourceCount(0)

    def test_anonymous_cannot_delete(self):
        source = self.make_source()
        self.app.delete('/v1/sources/%s' % source.id, status=403)
        self.assertSourceCount(1)

    def test_other_people_stuff(self):
        source = self.make_source(producer_id='abc')
        self.app.delete('/v1/sources/%s' % source.id,
                        headers={'X-ODE-Producer-Id': '123'},
                        status=404)
        self.assertSourceCount(1)

    def test_create_source(self):
        sources_info = {
            'collection': {
                'items': [
                    {'data': {'url': u'http://example.com/mysource'}}
                ]
            }
        }
        self.app.post_json('/v1/sources', sources_info, headers={
            'X-ODE-Producer-Id': '123'
        })
        source = DBSession.query(Source).one()
        self.assertEqual(source.url, u'http://example.com/mysource')

    def test_url_is_required(self):
        sources_info = {'sources': [{'url': u'\t  \r '}]}
        self.app.post_json('/v1/sources', sources_info, headers={
            'X-ODE-Producer-Id': '123'
        }, status=400)
        self.assertSourceCount(0)

    def test_anonymous_cannot_create(self):
        sources_info = {'sources': [{'url': u'http://example.com/mysource'}]}
        self.app.post_json('/v1/sources', sources_info, status=403)
        self.assertSourceCount(0)

    def test_update_source(self):
        source = self.make_source()
        response = self.app.put_json(
            '/v1/sources/%s' % source.id,
            {'url': 'http://example.com/myothersource'},
            headers={'X-ODE-Producer-Id': '123'})
        self.assertEqual(response.json['status'], 'updated')

    def test_update_required_producer_id(self):
        source = self.make_source()
        self.app.put_json('/v1/sources/%s' % source.id, {'url': 'whatever'},
                          status=403)

    def test_cannot_update_other_people_stuff(self):
        source = self.make_source(producer_id='abc')
        response = self.app.put_json('/v1/sources/%s' % source.id,
                                     {'url': 'http://example.com'},
                                     status=404,
                                     headers={'X-ODE-Producer-Id': '123'})
        self.assertEqual(response.json['status'], 404)

    def test_get_source_list(self):
        self.make_source(u"http://example.com/mysource")
        self.make_source(u"http://example.com/myothersource")
        response = self.app.get('/v1/sources')
        self.assertEqual(len(response.json['collection']['items']), 2)

    def test_valid_limit(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?limit=5')
        self.assertEqual(len(response['collection']['items']), 5)

    def test_invalid_limit(self):
        response = self.app.get('/v1/sources?limit=BOGUS', status=400)
        self.assertErrorMessage(response, '"BOGUS" is not a number')

    def test_valid_offset(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?offset=5')
        item = response['collection']['items'][0]
        self.assertEqual(item['data']['url'], 'http://example.com/feed6')

    def test_invalid_offset(self):
        response = self.app.get('/v1/sources?offset=BOGUS', status=400)
        self.assertErrorMessage(response, '"BOGUS" is not a number')

    def test_offset_and_limit(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?offset=5&limit=3')
        collection = response['collection']
        items = collection['items']
        self.assertEqual(collection['total_count'], 10)
        self.assertEqual(len(items), 3)
        self.assertEqual(collection['current_count'], 3)
        self.assertEqual(items[0]['data']['url'], 'http://example.com/feed6')
        self.assertEqual(items[-1]['data']['url'], 'http://example.com/feed8')
