#!/usr/bin/env python

import io
import os
from setuptools import setup, find_packages


def read(filename):
    with io.open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


setup(
    name="form_designer",
    version=__import__("form_designer").__version__,
    description="Form Designer",
    long_description=read("README.rst"),
    author="Matthias Kestenholz",
    author_email="mk@feinheit.ch",
    url="https://github.com/feincms/form_designer/",
    license="BSD License",
    platforms=["OS Independent"],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=["django-admin-ordering", "six", "xlsxdocument"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
    ],
    zip_safe=False,
)
