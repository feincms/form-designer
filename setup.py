#!/usr/bin/env python

from distutils.core import setup
import os
import setuplib

packages, package_data = setuplib.find_packages('form_designer')

setup(name='FeinCMS',
    version=__import__('form_designer').__version__,
    description='Form Designer - a simple form designer for FeinCMS',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/feincms/form_designer/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=packages,
    package_data=package_data,
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
