from functools import partial

from django import forms
from django.apps import apps
from django.utils.translation import gettext_lazy as _


def disallow_choices(field):
    if field.choices:
        raise forms.ValidationError(
            _("You can't specify choices for %s fields") % field.type
        )


def require_choices(field):
    if not field.choices:
        raise forms.ValidationError(
            _("Please specify choices for %s fields") % field.type
        )


FIELD_TYPES = [
    {
        "type": "text",
        "verbose_name": _("text"),
        "field": forms.CharField,
        "clean_field": [disallow_choices],
    },
    {
        "type": "email",
        "verbose_name": _("email address"),
        "field": forms.EmailField,
        "clean_field": [disallow_choices],
    },
    {
        "type": "longtext",
        "verbose_name": _("long text"),
        "field": partial(forms.CharField, widget=forms.Textarea),
        "clean_field": [disallow_choices],
    },
    {
        "type": "checkbox",
        "verbose_name": _("checkbox"),
        "field": partial(forms.BooleanField, required=False),
        "clean_field": [disallow_choices],
    },
    {
        "type": "select",
        "verbose_name": _("select"),
        "field": partial(forms.ChoiceField, required=False),
        "clean_field": [require_choices],
    },
    {
        "type": "radio",
        "verbose_name": _("radio"),
        "field": partial(forms.ChoiceField, widget=forms.RadioSelect),
        "clean_field": [require_choices],
    },
    {
        "type": "multiple-select",
        "verbose_name": _("multiple select"),
        "field": partial(
            forms.MultipleChoiceField, widget=forms.CheckboxSelectMultiple
        ),
        "clean_field": [require_choices],
    },
    {
        "type": "date",
        "verbose_name": _("date"),
        "field": partial(
            forms.DateField, widget=forms.DateInput(attrs={"type": "date"})
        ),
        "clean_field": [disallow_choices],
    },
    {
        "type": "hidden",
        "verbose_name": _("hidden"),
        "field": partial(forms.CharField, widget=forms.HiddenInput),
        "clean_field": [disallow_choices],
    },
]

# Add recaptcha field if available
if apps.is_installed("django_recaptcha"):  # pragma: no cover
    try:
        from django_recaptcha.fields import ReCaptchaField
        from django_recaptcha.widgets import ReCaptchaV2Checkbox, ReCaptchaV3
    except ImportError:
        pass
    else:
        FIELD_TYPES.append(
            {
                "type": "recaptcha",
                "verbose_name": _("reCAPTCHA v2"),
                "field": partial(ReCaptchaField, widget=ReCaptchaV2Checkbox),
            }
        )
        FIELD_TYPES.append(
            {
                "type": "recaptcha-v3",
                "verbose_name": _("reCAPTCHA v3"),
                "field": partial(ReCaptchaField, widget=ReCaptchaV3),
            }
        )


# Add django-simple-captcha field if available
if apps.is_installed("captcha"):  # pragma: no cover
    try:
        from captcha.fields import CaptchaField
    except ImportError:
        pass
    else:
        FIELD_TYPES.append(
            {
                "type": "simple captcha",
                "verbose_name": _("Simple CAPTCHA"),
                "field": CaptchaField,
            }
        )

if apps.is_installed("mosparo_django"):
    try:
        from mosparo_django.fields import MosparoField
    except ImportError:
        pass
    else:
        FIELD_TYPES.append(
            {
                "type": "mosparo captcha",
                "verbose_name": _("Mosparo Captcha"),
                "field": MosparoField,
            }
        )
