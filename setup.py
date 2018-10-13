from os.path import join, dirname
from setuptools import setup, find_packages


def read(fname):
    return open(join(dirname(__file__), fname)).read()


config = {
    'name': "anyconnect",
    'version': "0.2",
    'author': "Walter Oggioni",
    'author_email': "oggioni.walter@gmail.com",
    'description': ("csd wrapper scritp to use with Cisco's VPNs"),
    'long_description': '',
    'license': "MIT",
    'keywords': "build",
    'url': "https://github.com/oggio88/anyconnect",
    'packages': ['anyconnect'],
    'include_package_data': True,
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
    "entry_points": {
        'console_scripts': [
            'py-csd-wrapper=anyconnect.wrapper:run',
        ],
    }
}
setup(**config)
