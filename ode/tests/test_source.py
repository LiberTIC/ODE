from unittest import TestCase

from ode.models import DBSession, Source
from ode.tests import BaseTestMixin
from ode.deserializers import data_list_to_dict


class TestSource(BaseTestMixin, TestCase):

    def assertSourceCount(self, count):
        self.assertEqual(DBSession.query(Source).count(), count)

    def test_get_source(self):
        source = self.make_source()

        response = self.app.get('/v1/sources/%s' % source.id)

        source_data = response.json['collection']['items'][0]['data']
        data_dict = data_list_to_dict(source_data)
        self.assertEqual(data_dict['url'], 'http://example.com')

        source_href = response.json['collection']['items'][0]['href']
        self.assertEqual(source_href,
                         'http://localhost/v1/sources/%s' % source.id)

    def test_delete_source(self):
        source = self.make_source(provider_id=123)

        self.app.delete('/v1/sources/%s' % source.id,
                        headers={'X-ODE-Provider-Id': '123'},
                        status=204)

        self.assertSourceCount(0)

    def test_anonymous_cannot_delete(self):
        source = self.make_source()
        self.app.delete('/v1/sources/%s' % source.id, status=403)
        self.assertSourceCount(1)

    def test_other_people_stuff(self):
        source = self.make_source(provider_id='abc')
        self.app.delete('/v1/sources/%s' % source.id,
                        headers={'X-ODE-Provider-Id': '123'},
                        status=404)
        self.assertSourceCount(1)

    def test_create_source(self):
        sources_info = {
            'template': {
                'data': [
                    {'name': 'url', 'value': u'http://example.com/mysource'},
                    {'name': 'active', 'value': True},
                ]
            }
        }
        response = self.app.post_json(
            '/v1/sources',
            sources_info, headers={'X-ODE-Provider-Id': '123'},
            status=201)
        source = DBSession.query(Source).one()
        self.assertEqual(response.headers['location'],
                         'http://localhost/v1/sources/%s' % source.id)
        self.assertEqual(source.url, u'http://example.com/mysource')
        self.assertEqual(source.active, True)

    def test_url_is_required(self):
        sources_info = {'sources': [{'url': u'\t  \r '}]}
        self.app.post_json('/v1/sources', sources_info, headers={
            'X-ODE-Provider-Id': '123'
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
            {
                'template': {
                    'data': [
                        {'name': 'url',
                         'value': 'http://example.com/myothersource'},
                        {'name': 'active', 'value': False}
                    ]
                }
            },
            headers={'X-ODE-Provider-Id': '123'})
        self.assertEqual(response.json['status'], 'updated')
        source = DBSession.query(Source).one()
        self.assertEqual(source.url, u'http://example.com/myothersource')
        self.assertEqual(source.active, False)

    def test_update_required_provider_id(self):
        source = self.make_source()
        self.app.put_json('/v1/sources/%s' % source.id,
                          {'url': {'value': 'whatever'}},
                          status=403)

    def test_cannot_update_other_people_stuff(self):
        source = self.make_source(provider_id='abc')
        response = self.app.put_json(
            '/v1/sources/%s' % source.id,
            {
                'template': {
                    'data': [
                        {'name': 'url', 'value': 'http://example.com'}
                    ]
                }
            },
            status=404,
            headers={'X-ODE-Provider-Id': '123'})
        self.assertEqual(response.json['status'], 404)

    def test_get_source_list(self):
        source1 = self.make_source(u"http://example.com/mysource")
        source2 = self.make_source(u"http://example.com/myothersource")
        self.make_source(u"http://example.com/hersource", provider_id='456')

        response = self.app.get('/v1/sources',
                                headers={'X-ODE-Provider-Id': '123'})

        self.assertEqual(response.json['collection']['href'],
                         'http://localhost/v1/sources')
        items = response.json['collection']['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(data_list_to_dict(items[0]['data'])['id'],
                         source1.id)
        self.assertEqual(items[0]['href'],
                         'http://localhost/v1/sources/%s' % source1.id)
        self.assertEqual(data_list_to_dict(items[1]['data'])['id'],
                         source2.id)
        self.assertEqual(items[1]['href'],
                         'http://localhost/v1/sources/%s' % source2.id)

    def test_valid_limit(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?limit=5',
                                     headers={'X-ODE-Provider-Id': '123'})
        self.assertEqual(len(response['collection']['items']), 5)

    def test_invalid_limit(self):
        response = self.app.get('/v1/sources?limit=BOGUS', status=400,
                                headers={'X-ODE-Provider-Id': '123'})
        self.assertErrorMessage(response, '"BOGUS" is not a number')

    def test_valid_offset(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?offset=5',
                                     headers={'X-ODE-Provider-Id': '123'})
        item = response['collection']['items'][0]
        self.assertEqual(data_list_to_dict(item['data'])['url'],
                         'http://example.com/feed6')

    def test_invalid_offset(self):
        response = self.app.get('/v1/sources?offset=BOGUS', status=400,
                                headers={'X-ODE-Provider-Id': '123'})
        self.assertErrorMessage(response, '"BOGUS" is not a number')

    def test_offset_and_limit(self):
        for i in range(1, 11):
            self.make_source(u"http://example.com/feed%s" % i)
        response = self.app.get_json('/v1/sources?offset=5&limit=3',
                                     headers={'X-ODE-Provider-Id': '123'})
        collection = response['collection']
        items = collection['items']
        self.assertEqual(collection['total_count'], 10)
        self.assertEqual(len(items), 3)
        self.assertEqual(collection['current_count'], 3)
        self.assertEqual(data_list_to_dict(items[0]['data'])['url'],
                         'http://example.com/feed6')
        self.assertEqual(data_list_to_dict(items[-1]['data'])['url'],
                         'http://example.com/feed8')
