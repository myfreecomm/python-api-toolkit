from distutils.core import setup

setup(name='api_toolkit',
      version='0.2',
      packages=['api_toolkit'],
      install_requires=[
          'requests>=1.2.3'
      ],
      tests_require=['vcrpy==0.0.3'],
     )
