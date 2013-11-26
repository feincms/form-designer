from django import forms
from django.conf import settings
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _


FIELD_TYPES = [
    ('text', _('text'), forms.CharField),
    ('email', _('e-mail address'), forms.EmailField),
    ('longtext', _('long text'), curry(
        forms.CharField,
        widget=forms.Textarea,
    )),
    ('checkbox', _('checkbox'), curry(
        forms.BooleanField,
        required=False,
    )),
    ('select', _('select'), curry(
        forms.ChoiceField,
        required=False,
    )),
    ('radio', _('radio'), curry(
        forms.ChoiceField,
        widget=forms.RadioSelect,
    )),
    ('multiple-select', _('multiple select'), curry(
        forms.MultipleChoiceField,
        widget=forms.CheckboxSelectMultiple,
    )),
    ('hidden', _('hidden'), curry(
        forms.CharField,
        widget=forms.HiddenInput,
    )),
]

# Add recaptcha field if available
if 'captcha' in settings.INSTALLED_APPS:
    try:
        from captcha.fields import ReCaptchaField
    except ImportError:
        pass
    else:
        FIELD_TYPES.append((
            'recaptcha',
            _('recaptcha'),
            curry(
                ReCaptchaField,
                attrs={'theme': 'clean'},
            ),
        ))
