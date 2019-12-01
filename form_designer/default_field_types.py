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
        "type": "hidden",
        "verbose_name": _("hidden"),
        "field": partial(forms.CharField, widget=forms.HiddenInput),
        "clean_field": [disallow_choices],
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
