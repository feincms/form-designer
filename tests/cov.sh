#!/bin/sh
venv/bin/coverage run --branch --include="*form_designer/*" --omit="*tests*" ./manage.py test testapp
venv/bin/coverage html
