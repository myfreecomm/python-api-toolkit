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


    def test_should_load_resource_informations_on_load(self):
        with vcr.use_cassette('tests/cassettes/domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {
                    'accept': 'application/json',
                    'Content-Length': '0',
                    'Content-Type': 'application/json',
                }
            )


        self.assertEqual(resource.resource_data, response.json())

    def test_should_have_a_valid_session_on_load(self):
        with vcr.use_cassette('tests/cassettes/domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

        self.assertTrue(hasattr(resource, '_session'))

        session = resource._session

        self.assertEqual(session.auth, (TEST_API['USER'], TEST_API['PASSWORD']))
        self.assertEqual(session.headers['Accept'], 'application/json')
        self.assertEqual(session.headers['Content-Type'], 'application/json')
        self.assertEqual(session.headers['Content-Length'], '0')

    def test_should_create_collections_with_links(self):
        with vcr.use_cassette('tests/cassettes/domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {'accept': 'application/json'},
            )

        for item in response.links.keys():
            self.assertTrue(hasattr(resource, item))
            self.assertIsInstance(getattr(resource, item), Collection)
            self.assertEqual(getattr(resource, item).url, response.links[item]['url'])

    def test_created_collections_should_have_a_valid_session(self):
        with vcr.use_cassette('tests/cassettes/domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

        self.assertTrue(hasattr(resource, '_session'))

        session = resource.charge_accounts._session

        self.assertEqual(session.auth, (TEST_API['USER'], TEST_API['PASSWORD']))
        self.assertEqual(session.headers['Accept'], 'application/json')
        self.assertEqual(session.headers['Content-Type'], 'application/json')
        self.assertEqual(session.headers['Content-Length'], '0')

    def test_should_raise_404_if_wrong_url(self):
        with vcr.use_cassette('tests/cassettes/domain/wrong'):
            with self.assertRaises(requests.HTTPError):
                Resource.load(
                    url = 'http://localhost:8000/api/',
                    user = 'user',
                    password = 'pass',
                )


class TestResourceCollections(TestCase):

    def setUp(self):
        Resource.url_attribute_name = TEST_API['URL_ATTRIBUTE_NAME']

        with vcr.use_cassette('tests/cassettes/domain/load'):
            self.resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

    def test_all_should_return_a_list_of_the_charge_accounts_available(self):
        with vcr.use_cassette('tests/cassettes/charge_account/all'):
            charge_accounts = list(self.resource.charge_accounts.all())

        self.assertEqual(len(charge_accounts), 1)
        for item in charge_accounts:
            self.assertEqual(item._type, self.resource.charge_accounts._type)
            self.assertTrue(hasattr(item, TEST_API['URL_ATTRIBUTE_NAME']))

    def test_get_should_return_one_charge_account(self):
        with vcr.use_cassette('tests/cassettes/charge_account/get'):
            charge_account = list(self.resource.charge_accounts.all())[-1]

            charge_account = self.resource.charge_accounts.get(charge_account.uuid)

        self.assertEqual(charge_account._type, self.resource.charge_accounts._type)
        self.assertTrue(hasattr(charge_account, TEST_API['URL_ATTRIBUTE_NAME']))
        self.assertTrue(hasattr(charge_account, 'resource_data'))

