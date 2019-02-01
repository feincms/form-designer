from __future__ import unicode_literals

from functools import partial

from django import forms
from django.apps import apps
from django.utils.translation import ugettext_lazy as _


FIELD_TYPES = [
    ("text", _("text"), forms.CharField),
    ("email", _("e-mail address"), forms.EmailField),
    ("longtext", _("long text"), partial(forms.CharField, widget=forms.Textarea)),
    ("checkbox", _("checkbox"), partial(forms.BooleanField, required=False)),
    ("select", _("select"), partial(forms.ChoiceField, required=False)),
    ("radio", _("radio"), partial(forms.ChoiceField, widget=forms.RadioSelect)),
    (
        "multiple-select",
        _("multiple select"),
        partial(forms.MultipleChoiceField, widget=forms.CheckboxSelectMultiple),
    ),
    ("hidden", _("hidden"), partial(forms.CharField, widget=forms.HiddenInput)),
]

# Add recaptcha field if available
if apps.is_installed("captcha"):  # pragma: no cover
    try:
        from captcha.fields import ReCaptchaField
    except ImportError:
        pass
    else:
        FIELD_TYPES.append(
            (
                "recaptcha",
                _("recaptcha"),
                partial(ReCaptchaField, attrs={"theme": "clean"}),
            )
        )
