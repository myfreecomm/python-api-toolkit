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
    def make(cls, user, password):
        session = requests.Session()
        session.auth = (user, password)
        session.headers.update(cls.default_headers)

        return session


class Resource(object):
    url_attribute_name = 'url'
    _session = None
    session_factory = SessionFactory

    def __repr__(self):
        return '<api_toolkit.Resource type="%s">' % self.__class__

    def __init__(self, data, **kwargs):
        self.resource_data = data
        self._links = kwargs.get('links', {})
        self._session = kwargs.get('session', self._session)
        self._allowed_methods = kwargs.get('allowed_methods', ALL_METHODS)

        self.prepare_collections()

    @classmethod
    def load(cls, url, **kwargs):
        session = kwargs.get('session')

        if session is None:
            user = kwargs.get('user', '')
            password = kwargs.get('password', '')

            session = cls.session_factory.make(user, password)

        response = session.get(url)
        response.raise_for_status()

        instance = cls(
            data=response.json(),
            links=response.links,
            session=session,
        )
        instance.url = url

        instance._response = response

        return instance

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

    @url.setter
    def url(self, value):
        self.resource_data[self.url_attribute_name] = value

    @property
    def etag(self):
        return self.resource_data.get('etag') or self._response.get('etag')

    def prepare_collections(self):
        for item in self._links.values():
            link_name = item['rel']
            link_url = item['url']
            link_collection = Collection(
                link_url, session=self._session
            )

            setattr(self, link_name, link_collection)

    def save(self):
        if 'PUT' not in self._allowed_methods:
            raise ValueError('This resource cannot be saved.')

        dumped_data = json.dumps(self.resource_data)
        headers = {
            'Content-Length': str(len(dumped_data))
        }
        if self.resource_data.has_key('etag'):
            headers.update({'If-Match': self.etag})

        response = self._session.put(
            self.url,
            data=dumped_data,
            headers=headers,
        )
        response.raise_for_status()

        response = self._session.get(self.url)
        response.raise_for_status()

        self.resource_data = response.json()
        self._links=response.links

        return self

    def delete(self):
        if 'DELETE' not in self._allowed_methods:
            raise ValueError('This resource cannot be deleted.')

        headers = {}
        if self.etag:
            headers.update({'If-Match': self.etag})
        response = self._session.delete(self.url, headers=headers)
        response.raise_for_status()


class Collection(object):
    session_factory = SessionFactory

    def __repr__(self):
        return '<api_toolkit.Collection type="%s">' % self.__class__

    def __init__(self, url, **kwargs):
        self.url = url
        self._session = kwargs.get('session')
        self.resource_class = kwargs.get('resource_class', Resource)

        if self._session is None:
            user = kwargs.get('user', '')
            password = kwargs.get('password', '')

            self._session = self.session_factory.make(user, password)

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
                instance = self.resource_class(
                    data=item, session=self._session,
                    allowed_methods=response.headers.get('Allow', None),
                )
                yield instance

            if not response.links.has_key('next'):
                break

            url = response.links['next']['url']

    def get(self, identifier, append_slash=True):
        if 'GET' not in self._allowed_methods:
            raise ValueError('This collection cannot be loaded.')

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
            instance = self.resource_class(
                data=response.json(),
                links=response.links,
                session=self._session,
            )
            instance.url = self.url
        
            instance._response = response

        except ValueError:
            instance = self.resource_class.load(response.headers['Location'], session=self._session)

        return instance
