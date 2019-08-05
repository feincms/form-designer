from __future__ import unicode_literals

from functools import partial

from django import forms
from django.apps import apps
from django.utils.translation import ugettext_lazy as _


FIELD_TYPES = [
    {"type": "text", "verbose_name": _("text"), "field": forms.CharField},
    {"type": "email", "verbose_name": _("e-mail address"), "field": forms.EmailField},
    {
        "type": "longtext",
        "verbose_name": _("long text"),
        "field": partial(forms.CharField, widget=forms.Textarea),
    },
    {
        "type": "checkbox",
        "verbose_name": _("checkbox"),
        "field": partial(forms.BooleanField, required=False),
    },
    {
        "type": "select",
        "verbose_name": _("select"),
        "field": partial(forms.ChoiceField, required=False),
    },
    {
        "type": "radio",
        "verbose_name": _("radio"),
        "field": partial(forms.ChoiceField, widget=forms.RadioSelect),
    },
    {
        "type": "multiple-select",
        "verbose_name": _("multiple select"),
        "field": partial(
            forms.MultipleChoiceField, widget=forms.CheckboxSelectMultiple
        ),
    },
    {
        "type": "hidden",
        "verbose_name": _("hidden"),
        "field": partial(forms.CharField, widget=forms.HiddenInput),
    },
]

# Add recaptcha field if available
if apps.is_installed("captcha"):  # pragma: no cover
    try:
        from captcha.fields import ReCaptchaField
        from captcha.widgets import ReCaptchaV2Checkbox
    except ImportError:
        pass
    else:
        FIELD_TYPES.append(
            {
                "type": "recaptcha",
                "verbose_name": _("recaptcha"),
                "field": partial(ReCaptchaField, widget=ReCaptchaV2Checkbox),
            }
        )
