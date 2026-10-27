import re
from functools import partial

from django import forms
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe
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


def validate_tag(field):
    if field.default_value and not re.fullmatch(r"[a-z][a-z0-9]*", field.default_value):
        raise forms.ValidationError(
            _("The default value of %s fields has to be an HTML tag name") % field.type
        )


class DivWidget(forms.Widget):
    """Renders just a DIV"""

    def __init__(self, classes=(), text="", tag="div", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes = classes
        self.text = text
        self.tag = tag

    def render(self, name, value, attrs=None, renderer=None):
        classes = " ".join(value for value, label in self.classes)
        return format_html(
            "<{tag}{attrs}>{text}</{tag}>",
            tag=self.tag,
            attrs=flatatt({"class": classes} if classes else {}),
            # The title is HTML on purpose, only administrators can edit it
            text=mark_safe(self.text),
        )


class DIVField(forms.Field):
    """
    Renders a DIV (or other tag) by totally misusing some of the fields.
        `title` is the text content of the tag,
        `choices` is a list of classes for the `class` attr,
        `default_value`, if specified, overrides the tag of the field (default DIV),
    """

    choices = ()

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", ())
        kwargs["required"] = False
        kwargs["widget"] = DivWidget(
            text=kwargs.get("label"),  # Misuse `label` as text content
            tag=kwargs.get("initial") or "div",  # Misuse `initial` as tag
            classes=choices,  # Misuse `choices` for css classes
        )
        super().__init__(*args, **kwargs)
        self.label = ""


FIELD_TYPES = [
    {
        "type": "text",
        "verbose_name": _("text"),
        "field": forms.CharField,
    },
    {
        "type": "email",
        "verbose_name": _("email address"),
        "field": forms.EmailField,
    },
    {
        "type": "longtext",
        "verbose_name": _("long text"),
        "field": partial(forms.CharField, widget=forms.Textarea),
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
    {
        "type": "number",
        "verbose_name": _("number"),
        "field": partial(forms.CharField, widget=forms.NumberInput),
    },
    {
        "type": "statictext",
        "verbose_name": _("static text"),
        "field": DIVField,
        "clean_field": [validate_tag],
        "no-data": True,
    },
]


def recaptcha_versions():
    # The keys only work with one version, but nothing tells us which
    version = getattr(settings, "FORM_DESIGNER_RECAPTCHA_VERSION", None)
    if version is None:
        return {"v2", "v3"}
    if version not in {"v2", "v3"}:
        raise ImproperlyConfigured(
            f'FORM_DESIGNER_RECAPTCHA_VERSION must be "v2" or "v3", not {version!r}'
        )
    return {version}


# Add recaptcha field if available
if apps.is_installed("django_recaptcha"):  # pragma: no cover
    try:
        from django_recaptcha.fields import ReCaptchaField
        from django_recaptcha.widgets import ReCaptchaV2Checkbox, ReCaptchaV3
    except ImportError:
        pass
    else:
        versions = recaptcha_versions()
        if "v2" in versions:
            FIELD_TYPES.append(
                {
                    "type": "recaptcha",
                    "verbose_name": _("reCAPTCHA v2"),
                    "field": partial(ReCaptchaField, widget=ReCaptchaV2Checkbox),
                }
            )
        if "v3" in versions:
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
