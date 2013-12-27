#coding: utf-8
import json
import requests

__all__ = ['Resource', 'Collection']


class Resource(object):
    url_attribute_name = 'url'
    _session = None

    def __repr__(self):
        return '<api_toolkit.Resource type="%s">' % self._type

    def __init__(self, data, **kwargs):
        self.resource_data = data
        self._links = kwargs.get('links', {})
        self._type = kwargs.get('type', None)
        self._session = kwargs.get('session', self._session)

        self.prepare_collections()

    @classmethod
    def load(cls, url, **kwargs):
        session = kwargs.get('session')

        if session is None:
            user = kwargs.get('user', '')
            password = kwargs.get('password', '')

            session = requests.Session()
            session.auth = (user, password)
            session.headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Content-Length': '0',
                'User-Agent': 'api_toolkit',
            })

        response = session.get(url)
        response.raise_for_status()

        instance = cls(
            data=response.json(),
            type=kwargs.get('type'),
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
                link_url, type=link_name, session=self._session
            )

            setattr(self, link_name, link_collection)

    def save(self):
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
        headers = {}
        if self.etag:
            headers.update({'If-Match': self.etag})
        response = self._session.delete(self.url, headers=headers)
        response.raise_for_status()


class Collection(object):
    url = None
    resource_class = Resource
    _session = None
    _type = 'entrypoint'

    def __repr__(self):
        return '<api_toolkit.Collection type="%s">' % self._type

    def __init__(self, url, **kwargs):
        self.url = url
        self._type = kwargs.get('type')
        self._session = kwargs.get('session')

        if self._session is None:
            user = kwargs.get('user', '')
            password = kwargs.get('password', '')

            self._session = requests.Session()
            self._session.auth = (user, password)
            self._session.headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Content-Length': '0',
                'User-Agent': 'api_toolkit',
            })

    def all(self):
        url = self.url
        while True:
            response = self._session.get(url)
            for item in response.json():
                instance = self.resource_class(
                    data=item, type=self._type, session=self._session
                )
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
        return self.resource_class.load(url, type=self._type, session=self._session)

    def create(self, **kwargs):
        resource_data = json.dumps(kwargs)
        response = self._session.post(
            self.url,
            headers={'content-length': str(len(resource_data))},
            data=resource_data
        )

        response.raise_for_status()
        return self.resource_class.load(response.headers['Location'], type=self._type, session=self._session)

