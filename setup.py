# -*- coding: utf-8 -*-
import setuptools
from os.path import join, dirname

setuptools.setup(
    name="api_toolkit",
    version="0.2",
    packages=["api_toolkit"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=['requests>=1.2.3']
    tests_require=['vcrpy==0.0.3'],
    test_suite='api_toolkit.tests',
    author="vitormazzi",
    author_email="vitormazzi@gmail.com",
    url="http://github.com/myfreecomm/python-api-toolkit",
    license="Apache 2.0",
    description="A library which simplifies the creation of clients for REST webservices.",
    long_description=open(join(dirname(__file__), "README.md")).read(),
    keywords="python rest webservices",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
)
