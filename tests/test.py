from unittest import TestCase
import vcr
import requests

from charging_toolkit import Resource, Collection

TEST_API = {
    'ENTRYPOINT': 'http://localhost:8000/domain/',
    'USER': '',
    'PASSWORD': '1+OC7QHjQG6H9ITrLQ7CWw==',
    'URL_ATTRIBUTE_NAME': 'uri',
}



class TestResourceLoad(TestCase):

    def setUp(self):
        Resource.url_attribute_name = TEST_API['URL_ATTRIBUTE_NAME']

        with vcr.use_cassette('tests/cassettes/domain'):
            self.resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

    def test_should_load_resource_informations_on_load(self):
        with vcr.use_cassette('tests/cassettes/domain'):
            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {'accept': 'application/json'},
            )


        self.assertEqual(self.resource.resource_data, response.json())

    def test_should_have_a_valid_session_on_load(self):
        self.assertTrue(hasattr(self.resource, '_session'))

        session = self.resource._session

        self.assertEqual(session.auth, (TEST_API['USER'], TEST_API['PASSWORD']))
        self.assertEqual(session.headers['Accept'], 'application/json')
        self.assertEqual(session.headers['Content-Type'], 'application/json')
        self.assertEqual(session.headers['Content-Length'], '0')

    def test_should_create_collections_with_links(self):
        with vcr.use_cassette('tests/cassettes/domain'):
            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {'accept': 'application/json'},
            )

        for item in response.links.keys():
            self.assertTrue(hasattr(self.resource, item))
            self.assertIsInstance(getattr(self.resource, item), Collection)
            self.assertEqual(getattr(self.resource, item).url, response.links[item]['url'])

    def test_created_collections_should_have_a_valid_session(self):
        self.assertTrue(hasattr(self.resource, '_session'))

        session = self.resource.charge_accounts._session

        self.assertEqual(session.auth, (TEST_API['USER'], TEST_API['PASSWORD']))
        self.assertEqual(session.headers['Accept'], 'application/json')
        self.assertEqual(session.headers['Content-Type'], 'application/json')
        self.assertEqual(session.headers['Content-Length'], '0')

    def test_should_raise_404_if_wrong_url(self):
        with vcr.use_cassette('tests/cassettes/wrong_domain'):
            with self.assertRaises(requests.HTTPError):
                Resource.load(
                    url = 'http://localhost:8000/api/',
                    user = 'user',
                    password = 'pass',
                )


