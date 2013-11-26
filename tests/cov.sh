#!/bin/sh
coverage run --branch --include="*email_registration/*" --omit="*tests*" ./manage.py test testapp
coverage html
