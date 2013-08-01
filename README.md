Python-API-toolkit
==================
Python-API-toolkit is a module that focuses on dealing with REST APIs in a simple way. The API will need to follow some simple rules to be supported.


Demonstration
-------------
For example, using [Charging](https://github.com/myfreecomm/charging) with Python-API-toolkit.


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
     u'token: u'9kpJCaG/Qsui+G3s+0QcKA==',
     u'uri': u'http://sandbox.charging.financeconnect.com.br/account/domains/513e8442-0a4e-404c-b405-8681ca7e58b1/',
     u'uuid': u'513e8442-0a4e-404c-b405-8681ca7e58b1',
     u'zipcode': u'24020040'}
     >>> # You can, then, acess any keys from resource_data as attributes and treat the resource as an object.
     >>> entrypoint.address = u'New Address'
     >>> entrypoint.save()
     >>> list(entrypoint.charge_accounts.all())
     [<api_toolkit.Resource type="charge_accounts">, <api_toolkit.Resource type="charge_accounts">]
    

And every other Resource object operates the same way as the first:

     >>> for res in entrypoint.charge_accounts.all():
     ...     res.delete()
     

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

``pip install -e git+git@github.com:myfreecomm/python-api-toolkit#egg=python-api-toolkit``
