Python-API-toolkit
==================
Python-API-toolkit is a module that focuses on dealing with REST APIs in a simple way. The API will need to follow some simple rules to be supported.


Demonstration
-------------
For example, using [Charging](https://github.com/myfreecomm/charging) with Python-API-toolkit.

```python
    >>> from api_toolkit import Resource
    >>> print Resource.url_attribute_name
    'url'
    >>> Resource.url_attribute_name = 'uri'
    >>> entrypoint = Resource.load(
    ...     'http://sandbox.charging.financeconnect.com.br/domain/',
    ...     user='', password='1+OC7QHjQG6H9ITrLQ7CWw=='
    ... )
    >>> entrypoint.resource_data
    {u'address': u'Address',
     u'city_state': u'Niteroi/Rj',
     u'description': None,
     u'etag': u'da39a3ee5e6b4b0d3255bfef95601890afd80709',
     u'supplier_name': u'Gerardo Soares',
     u'token': u'9kpJCaG/Qsui+G3s+0QcKA==',
     u'uri': u'http://sandbox.charging.financeconnect.com.br/account/domains/513e8442-0a4e-404c-b405-8681ca7e58b1/',
     u'uuid': u'513e8442-0a4e-404c-b405-8681ca7e58b1',
     u'zipcode': u'24020040'}
     >>> # You can, then, acess any keys from resource_data as attributes and treat the resource as an object.
     >>> entrypoint.address = u'New Address'
     >>> entrypoint.save()
     >>> list(entrypoint.charge_accounts.all())
     [<api_toolkit.Resource type="charge_accounts">, <api_toolkit.Resource type="charge_accounts">]
```

And every other Resource object operates the same way as the first:
```python
     >>> for res in entrypoint.charge_accounts.all():
     ...     res.delete()
```

Requirements (for APIs)
-----------------------
If you want to support Python-API-toolkit in your API you'll have to follow three rules:

1. Your API should be RESTful.
2. You should implement the header Link.
3. Your API should accept JSON.


Github uses the header Link for its [API's pagination](http://developer.github.com/v3/#pagination). All we need is to extend that a bit. For instance: At [Charging](https://github.com/myfreecomm/charging) the [/domain/](http://sandbox.charging.financeconnect.com.br/domain/) has the following Link header:

    Link: <http://sandbox.charging.financeconnect.com.br/charge-accounts/>; rel="charge_accounts"


At pages where the pagination is present, like [/charge-accounts/](http://sandbox.charging.financeconnect.com.br/charge-accounts/), the Link header is presented like this:

    Link: <http://sandbox.charging.financeconnect.com.br/charge-accounts/banks/>; rel="banks",
          <http://sandbox.charging.financeconnect.com.br/charge-accounts/currencies/>; rel="currencies",
          <http://sandbox.charging.financeconnect.com.br/charge-accounts/?limit=10&page=2>; rel="next"


Requirements (for Clients)
--------------------------
Python-API-toolkit uses ```requests``` instead of the common ```HttpLib2```.


Install
-------
You can install Python-API-toolkit via ``pip`` or ``easy_install``. This project isn't on PyPi yet.

``$ pip install -e git+git@github.com:myfreecomm/python-api-toolkit#egg=python-api-toolkit``


Documentation
-------------
Python-API-toolkit uses two classes to expose the API in a friendly way, Resource and Collection.
The Resources are the API's objects and entrypoints, they are the entities you'll manipulate.
The Collections are just collections of the same Resource.
Python-API-toolkit defines GET and DELETE HTTP verbs to both, PUT to the Resource and POST to the Collection, right now all verbs will be allowed to each Resource or Collection, even if the API doens't.
Futurely the verbs will be limited to those the API responds via OPTIONS.

### Resource
Resources are the API's objects and entrypoints.

Resources are loaded initially, so you won't neet to GET the resources, most of the time. But you can always ``reload()`` them to Sync them up with the API server.
For example:
```python
    >>> from api_toolkit import Resource
    >>> res = Resource.load('http://example.com/api/user/', user='test', password='pass')
    >>> res.url
    'http://example.com/api/user/'
    >>> # The resource is loaded initially.
    >>> res.url = 'Nope!'
    >>> res.reload()
    >>> res.url
    'http://example.com/api/user/'
    >>> # The resource is synced up with the server.
```

But what if you want to PUT something at the API server's resource? All you have to do is treat the Resource as an object and call ``save()`` when you're done. Much like Django ORM's Models.
For instance:
```python
    >>> # We're reusing the resource loaded previously.
    >>> res.name = 'Test User'
    >>> res.save()
    >>> # The server accepted our changes.
    >>> res.reload()
    >>> res.name
    'Test User'
```
Note: If you try to change an attribute that can't be changed, the object will accept it just fine, but ``save()`` will raise an exception.
```python
    >>> res.url = 'http://example.com/submarine/'
    >>> res.save()
    HTTPError: 400 Client Error: Bad Request
```

And if you want to DELETE the resource, all you have to do is call ``delete()``.
```python
    >>> res.delete()
    >>> res.reload()
    HTTPError: 404 Client Error: Not Found
```
Note: The local instance won't be deleted as well. If the API accepts PUT as create all you have to do is call ``save()`` after you deleted the object.
```python
    >>> res.url
    'http://example.com/api/user/'
    >>> res.save()
    >>> res.reload()
```

Loaded resources also have their collections instantiated as attributes. To get the Tasks Collection related to this user, all you have to do is:
```python
    >>> res.tasks
    <api_toolkit.Collection type="tasks">
```

### Collection
Collections are the Resource managers. At collections you can list all Resources from that type, get a specific Resource from that type, create a new Resource or maybe delete all Resources from that type.

You can use ``all()`` to get all resources from the same type. For instance:
```python
    >>> # We're still utilizing the resource we defined earlier.
    >>> res.tasks
    <api_toolkit.Collection type="tasks">
    >>> list(res.tasks.all())
    [<api_toolkit.Resource type="tasks">, <api_toolkit.Resource type="tasks">]
    >>> # Note that all() returns a generator.
    >>> for resource in res.tasks.all()
    ...     print resource.url
    'http://example.com/api/users/tasks/1/'
    'http://example.com/api/users/tasks/2/'
```

To get a specific resource you can use ``get()``. ``get()`` takes the resource identifier as an argument (In 'http://example.com/api/users/tasks/1/' the identifier is '1'.
```python
    >>> first_resource = res.tasks.get('1')
    >>> first_resource.url
    'http://example.com/api/users/tasks/1/'
```

To create a new resource all you have to do is provide enough arguments to ``create()``. For example:
```python
    >>> new_resource = res.tasks.create(
    ...     description = 'Test task to be created.',
    ...     due_date = '07/10',
    ...     name = 'Task#01'
    ... )
```

And now, if we want to delete everything from the collection, we just call ``delete()``. TO BE IMPLEMENTED
```python
    >>> res.tasks.delete()
    >>> list(res.tasks.all())
    []
    >>> # Everything gone! Let's just save that resource we just created again...
    >>> new_resource.save()
    >>> list(res.tasks.all())
    [<api_toolkit.Resource type="tasks">]
```

