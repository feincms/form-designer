#!/usr/bin/env python

import os
from setuptools import setup, find_packages


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name='form_designer',
    version=__import__('form_designer').__version__,
    description='Form Designer - a simple form designer for FeinCMS',
    long_description=read('README.rst'),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/feincms/form_designer/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=find_packages(
        exclude=[],
    ),
    package_data={
        '': ['*.html', '*.txt'],
        'form_designer': [
            'locale/*/*/*.*',
            # 'static/form_designer/*.*',
            # 'static/form_designer/*/*.*',
            'templates/*.*',
            'templates/*/*.*',
            'templates/*/*/*.*',
            'templates/*/*/*/*.*',
        ],
    },
    install_requires=[
        'Django>=1.4.2',
        # Yes, form_designer can be used without FeinCMS.
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
    ],
)
