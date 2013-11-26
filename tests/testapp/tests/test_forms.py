import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.http import urlunquote

from form_designer.models import Form


class FormsTest(TestCase):
    def test_registration(self):
        pass
