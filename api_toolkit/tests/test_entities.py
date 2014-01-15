import os
from unittest import TestCase
import vcr
import requests

from helpers import use_cassette
from api_toolkit import Resource, Collection

__all__ = ['TestResourceLoad', 'TestCollections', 'TestResources']

TEST_API = {
    'ENTRYPOINT': 'http://sandbox.charging.financeconnect.com.br/domain/',
    'USER': '',
    'PASSWORD': '1+OC7QHjQG6H9ITrLQ7CWw==',
    'URL_ATTRIBUTE_NAME': 'uri',
}


class TestResourceLoad(TestCase):

    def setUp(self):
        Resource.url_attribute_name = TEST_API['URL_ATTRIBUTE_NAME']


    def test_should_load_resource_informations_on_load(self):
        with use_cassette('domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {
                    'Accept': 'application/json',
                    'Content-Length': '0',
                    'Content-Type': 'application/json',
                    'User-Agent': 'api_toolkit',
                }
            )

        self.assertEqual(resource.resource_data, response.json())

    def test_should_have_a_valid_session_on_load(self):
        with use_cassette('domain/load'):
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
        self.assertEqual(session.headers['User-Agent'], 'api_toolkit')

    def test_should_put_response_in_the_resource(self):
        with use_cassette('domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

        self.assertTrue(hasattr(resource, '_response'))
        self.assertTrue(isinstance(resource._response, requests.Response))

    def test_should_create_collections_with_links(self):
        with use_cassette('domain/load'):
            resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

            response = requests.get(
                url = TEST_API['ENTRYPOINT'],
                auth = ('', TEST_API['PASSWORD']),
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'api_toolkit',
                },
            )

        for item in response.links.keys():
            self.assertTrue(hasattr(resource, item))
            self.assertTrue(isinstance(getattr(resource, item), Collection))
            self.assertEqual(getattr(resource, item).url, response.links[item]['url'])

    def test_created_collections_should_have_a_valid_session(self):
        with use_cassette('domain/load'):
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
        with use_cassette('domain/wrong'):
            self.assertRaises(
                requests.HTTPError,
                Resource.load,
                url = 'http://sandbox.charging.financeconnect.com.br/api/',
                user = 'user',
                password = 'pass',
            )


class TestCollections(TestCase):

    def setUp(self):
        Resource.url_attribute_name = TEST_API['URL_ATTRIBUTE_NAME']

        with use_cassette('domain/load'):
            self.resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

    def test_all_should_return_a_list_of_the_charge_accounts_available(self):
        with use_cassette('charge_account/all'):
            charge_accounts = list(self.resource.charge_accounts.all())

        self.assertEqual(len(charge_accounts), 1)
        for item in charge_accounts:
            # TODO: volta aqui
            #self.assertEqual(item._type, self.resource.charge_accounts._type)
            self.assertTrue(hasattr(item, TEST_API['URL_ATTRIBUTE_NAME']))

    def test_get_should_return_one_resource(self):
        with use_cassette('charge_account/get'):
            charge_account = list(self.resource.charge_accounts.all())[-1]

            charge_account = self.resource.charge_accounts.get(charge_account.uuid)

        self.assertTrue(hasattr(charge_account, TEST_API['URL_ATTRIBUTE_NAME']))
        self.assertTrue(hasattr(charge_account, 'resource_data'))

    def test_resources_created_by_collections_should_have_a_valid_session(self):
        with use_cassette('charge_account/get'):
            charge_account = list(self.resource.charge_accounts.all())[-1]

            charge_account = self.resource.charge_accounts.get(charge_account.uuid)

        self.assertTrue(hasattr(charge_account, '_session'))
        session = charge_account._session

        self.assertEqual(session.auth, (TEST_API['USER'], TEST_API['PASSWORD']))
        self.assertEqual(session.headers['Accept'], 'application/json')
        self.assertEqual(session.headers['Content-Type'], 'application/json')
        self.assertEqual(session.headers['Content-Length'], '0')

    def test_create_should_instantiate_the_resource_with_the_returned_data(self):
        data = {
            'bank': '237',
            'name': 'Bradesco charge_account',
            'agreement_code': '1234',
            'portfolio_code': '11',
            'agency': {'number': 412, 'digit': ''},
            'account': {'number': 1432, 'digit': '6'},
            'national_identifier': '86271628000147',
        }

        with use_cassette('charge_account/create'):
            charge_account = self.resource.charge_accounts.create(**data)

        # this cassette has no Location in the response.
        self.assertFalse('Location' in charge_account._response.headers)

        self.assertTrue(isinstance(charge_account, Resource))

        for item in data.items():
            self.assertTrue(charge_account.resource_data.has_key(item[0]))
            self.assertEqual(charge_account.resource_data[item[0]], item[1])

        self.assertEqual(charge_account._session, self.resource.charge_accounts._session)

    def test_create_should_load_the_resource_via_the_location_header(self):
        data = {
            'bank': '237',
            'name': 'Bradesco charge_account',
            'agreement_code': '1234',
            'portfolio_code': '11',
            'agency': {'number': 412, 'digit': ''},
            'account': {'number': 1432, 'digit': '6'},
            'national_identifier': '86271628000147',
        }

        with use_cassette('charge_account/create_with_location'):
            charge_account = self.resource.charge_accounts.create(**data)

        self.assertEqual(charge_account._response.request.method, 'GET')

        self.assertTrue(isinstance(charge_account, Resource))

        for item in data.items():
            self.assertTrue(charge_account.resource_data.has_key(item[0]))
            self.assertEqual(charge_account.resource_data[item[0]], item[1])

        self.assertEqual(charge_account._session, self.resource.charge_accounts._session)


class TestResources(TestCase):

    def setUp(self):
        Resource.url_attribute_name = TEST_API['URL_ATTRIBUTE_NAME']

    def test_save_should_put_the_resource(self):
        with use_cassette('domain/load'):
            self.resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

        with use_cassette('charge_account/save'):
            charge_account = list(self.resource.charge_accounts.all())[-1]
            resource_data = charge_account.resource_data

            charge_account.supplier_name = 'Rubia'
            charge_account.address = 'Rua do BUSTV'
            charge_account.save()

        self.assertEqual(charge_account.resource_data.pop('supplier_name'), 'Rubia')
        self.assertEqual(charge_account.resource_data.pop('address'), 'Rua do BUSTV')

        self.assertEqual(resource_data, charge_account.resource_data)

    def test_delete_should_delete_the_resource(self):
        with use_cassette('domain/load'):
            self.resource = Resource.load(
                url = TEST_API['ENTRYPOINT'],
                user = TEST_API['USER'],
                password = TEST_API['PASSWORD'],
            )

        with use_cassette('charge_account/to_be_deleted'):
            charge_account = self.resource.charge_accounts.create(**{
                'bank': '237',
                'name': 'Charge Account to be deleted',
                'agreement_code': '1444',
                'portfolio_code': '12',
                'agency': {'number': 453, 'digit': ''},
                'account': {'number': 1633, 'digit': '1'},
                'national_identifier': '86271628000147',
            })

        uuid = charge_account.uuid

        with use_cassette('charge_account/delete'):
            charge_account.delete()
            self.assertRaises(requests.HTTPError, self.resource.charge_accounts.get, uuid)

    def test_setattr_should_update_resource_data_if_it_is_the_same_key(self):
        resource = Resource(
            first='first_value',
            second='second_value',
            session=requests.Session()
        )

        resource.first = 'new_value'

        self.assertRaises(AttributeError, object.__getattribute__, resource, 'first')

        self.assertTrue(resource.resource_data.has_key('first'))
        self.assertEqual(resource.resource_data['first'], 'new_value')

    def test_setattr_should_not_update_resource_data_if_the_key_is_not_present(self):
        resource = Resource(
            first='first_value',
            second='second_value',
            session=requests.Session()
        )

        resource.third = 'new_value'

        third = object.__getattribute__(resource, 'third')

        self.assertFalse(resource.resource_data.has_key('third'))
        self.assertEqual(third, 'new_value')

    def test_setattr_should_not_set_collections_at_resource_data(self):
        resource = Resource(
            first='first_value',
            second='second_value',
            session=requests.Session()
        )

        col = Collection('http://dummyurl.com/', type='type')
        resource.first = col

        first = object.__getattribute__(resource, 'first')

        self.assertTrue(resource.resource_data.has_key('first'))
        self.assertEqual(resource.resource_data['first'], 'first_value')
        self.assertEqual(first, col)

    def test_getattr_should_prioritize_instance_attributes(self):
        resource = Resource(
            first='first_value',
            session=requests.Session()
        )

        resource.second = 'instance_value'
        resource.resource_data.update({'second': 'dict_value'})

        self.assertEqual(resource.second, 'instance_value')
        self.assertEqual(resource.resource_data['second'], 'dict_value')
        self.assertEqual(object.__getattribute__(resource, 'second'), 'instance_value')
