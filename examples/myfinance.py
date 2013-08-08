import copy

import requests

from api_toolkit import Resource as BaseResource
from api_toolkit import Collection as BaseCollection

__all__ = ['Accounts']


class MyFinanceResource(BaseResource):
    _url = None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self.prepare_collections()


class PaginatedCollection(BaseCollection):
    resource_class = MyFinanceResource

    def all(self):
        url = self.url
        page = 1
        while True:
            response = self._session.get('{0}?page={1}'.format(url, page))
            response.raise_for_status()

            if len(response.json()) == 0:
                break

            for item in response.json():
                instance = self.resource_class(
                    data=item, type=self._type, session=self._session
                )
                instance.url = '{0}{1}/'.format(url, item.values()[0]['id'])
                yield instance

            page += 1


class NotPaginatedCollection(BaseCollection):
    resource_class = MyFinanceResource

    def all(self):
        response = self._session.get(self.url)
        response.raise_for_status()

        for item in response.json():
            instance = self.resource_class(
                data=item, type=self._type, session=self._session
            )
            instance.url = '{0}{1}/'.format(self.url, item.values()[0]['id'])
            yield instance


class Accounts(object):
    def __init__(self, url, token):
        self._session = requests.Session()
        self._session.auth = (token,'')
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Content-Length': '0',
        })

        self.url = url

    def all(self):
        response = self._session.get('{0}accounts'.format(self.url))
        response.raise_for_status()

        for item in response.json():
            instance = Account(
                item, type='accounts', session=copy.deepcopy(self._session)
            )
            instance.url = self.url
            yield instance


class Account(MyFinanceResource):
    def __init__(self, *args, **kwargs):
        super(Account, self).__init__(*args, **kwargs)
        self._session.headers.update({
            'ACCOUNT_ID': str(self.resource_data['account']['id'])
        })

    def prepare_collections(self):
        self.entities = NotPaginatedCollection(
            '{0}entities/'.format(self.url),
            type='entities', session=self._session
        )
        self.entities.resource_class= Entity

        self.people = PaginatedCollection(
            '{0}people/'.format(self.url),
            type='people', session=self._session
        )

        self.categories = NotPaginatedCollection(
            '{0}categories/'.format(self.url),
            type='categories', session=self._session
        )

        self.classification_centers = NotPaginatedCollection(
            '{0}classification_centers/'.format(self.url),
            type='classification_centers', session=self._session
        )


class Entity(MyFinanceResource):
    def prepare_collections(self):
        self.credit_cards = NotPaginatedCollection(
            '{0}credit_cards/'.format(self.url),
            type='credit_cards', session=self._session
        )
        self.credit_cards.resource_class = CreditCard

        self.deposit_accounts = NotPaginatedCollection(
            '{0}deposit_accounts/'.format(self.url),
            type='deposit_accounts', session=self._session
        )
        self.deposit_accounts.resource_class = DepositAccount

        self.payable_accounts = PaginatedCollection(
            '{0}payable_accounts/'.format(self.url),
            type='payable_accounts', session=self._session
        )

        self.receivable_accounts = PaginatedCollection(
            '{0}receivable_accounts/'.format(self.url),
            type='receivable_accounts', session=self._session
        )

        self.attachments = PaginatedCollection(
            '{0}attachments/'.format(self.url),
            type='attachments', session=self._session
        )


class DepositAccount(MyFinanceResource):
    def prepare_collections(self):
        self.financial_transactions = PaginatedCollection(
            '{0}financial_transactions/'.format(self.url),
            type='financial_transactions', session=self._session
        )

        self.bank_statements = NotPaginatedCollection(
            '{0}bank_statements/'.format(self.url),
            type='bank_statements', session=self._session
        )


class CreditCard(MyFinanceResource):
    def prepare_collections(self):
        self.transactions = NotPaginatedCollection(
            '{0}transactions/'.format(self.url),
            type='transactions', session=self._session
        )

