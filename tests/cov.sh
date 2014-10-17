#!/bin/sh
coverage run --branch --include="*form_designer/*" --omit="*tests*" ./manage.py test testapp
coverage html
