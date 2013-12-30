#coding: utf-8
import json
import requests

__all__ = ['Resource', 'Collection']

ALL_METHODS = 'HEAD, OPTIONS, GET, PUT, POST, DELETE'


class SessionFactory(object):
    default_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Content-Length': '0',
        'User-Agent': 'api_toolkit',
    }

    @classmethod
    def make(cls, **credentials):
        session = requests.Session()
        session.auth = cls.get_auth(**credentials)
        session.headers.update(cls.default_headers)

        return session

    @classmethod
    def get_auth(cls, **credentials):
        return (
            credentials.get('user', ''),
            credentials.get('password', '')
        )


class Resource(object):
    url_attribute_name = 'url'
    session_factory = SessionFactory

    _response = None
    _meta = {
        'allowed_methods': ALL_METHODS,
        'etag': None,
        'links': {},
        'fields': None,
    }

    def __repr__(self):
        return '<api_toolkit.Resource type="%s">' % self.__class__

    def __init__(self, **kwargs):
        self.resource_data = kwargs

    @classmethod
    def from_response(cls, response, session):
        instance = cls(**response.json())
        instance._session = session
        instance.response = response

        return instance

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = response
        self._meta['links'] = response.links
        self._meta['etag'] = response.headers.get('etag', None)
        self._meta['allowed_methods'] = response.headers.get('Allow', ALL_METHODS)

        self.prepare_collections()

    @classmethod
    def load(cls, url, **kwargs):
        session = kwargs.pop('session', cls.session_factory.make(**kwargs))

        response = session.get(url)
        response.raise_for_status()

        return cls.from_response(response, session)

    def __setattr__(self, name, value):
        if (hasattr(self, 'resource_data')
            and self.resource_data.has_key(name)
            and not isinstance(value, Collection)):

            self.resource_data[name] = value
        else:
            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self, 'resource_data')[name]

    @property
    def url(self):
        return self.resource_data.get(self.url_attribute_name)

    def prepare_collections(self):
        for item in self._meta['links'].values():
            link_name = item['rel']
            link_url = item['url']
            link_collection = Collection(
                link_url, session=self._session
            )

            setattr(self, link_name, link_collection)

    def load_options(self):
        if self._session and self.url:
            self.response = self._session.options(self.url)
        else:
            raise ValueError('Cannot load options for this instance')

    def save(self):
        if 'PUT' not in self._meta['allowed_methods']:
            raise ValueError('This resource cannot be saved.')

        if self._meta['fields'] is None:
            dumped_data = json.dumps(self.resource_data)
        else:
            filtered_data = dict((k, v)
                for k, v in self.resource_data.items()
                if k in self._meta['fields']
            )
            dumped_data = json.dumps(filtered_data)

        headers = {
            'Content-Length': str(len(dumped_data))
        }
        if self._meta.get('etag'):
            headers.update({'If-Match': self._meta['etag']})

        response = self._session.put(
            self.url,
            data=dumped_data,
            headers=headers,
        )
        response.raise_for_status()

        try:
            instance = self.__class__.from_response(
                response=response, session=self._session
            )
        except ValueError:
            instance = self.__class__.load(self.url, session=self._session)

        return instance

    def delete(self):
        if 'DELETE' not in self._meta['allowed_methods']:
            raise ValueError('This resource cannot be deleted.')

        headers = {}
        if self._meta.get('etag'):
            headers.update({'If-Match': self._meta['etag']})

        response = self._session.delete(self.url, headers=headers)
        response.raise_for_status()


class Collection(object):
    session_factory = SessionFactory

    def __repr__(self):
        return '<api_toolkit.Collection type="%s">' % self.__class__

    def __init__(self, url, **kwargs):
        self.url = url
        self._session = kwargs.pop('session', self.session_factory.make(**kwargs))
        self.resource_class = kwargs.get('resource_class', Resource)

        self._allowed_methods = self.discover_allowed_methods()

    def discover_allowed_methods(self):
        response = self._session.options(self.url)
        return response.headers.get('Allow', ALL_METHODS)

    def all(self):
        if 'GET' not in self._allowed_methods:
            raise ValueError('This collection is not iterable.')

        url = self.url
        while True:
            response = self._session.get(url)
            for item in response.json():
                instance = self.resource_class(**item)
                instance._session = self._session
                instance.load_options()
                yield instance

            if not response.links.has_key('next'):
                break

            url = response.links['next']['url']

    def get(self, identifier, append_slash=True):
        if append_slash:
            url_template = '{0}{1}/'
        else:
            url_template = '{0}{1}'

        url = url_template.format(self.url, identifier)
        return self.resource_class.load(url, session=self._session)

    def create(self, **kwargs):
        if 'POST' not in self._allowed_methods:
            raise ValueError('No items can be created for this collection.')

        resource_data = json.dumps(kwargs)
        response = self._session.post(
            self.url,
            headers={'content-length': str(len(resource_data))},
            data=resource_data
        )

        response.raise_for_status()
        
        try:
            instance = self.resource_class.from_response(
                response=response, session=self._session
            )
        except ValueError:
            instance = self.resource_class.load(
                url=response.headers['Location'],
                session=self._session
            )

        return instance
