from __future__ import unicode_literals

from collections import OrderedDict
import datetime  # noqa
import json

from django import forms
from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import lazy
from django.utils.html import format_html, mark_safe
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from form_designer import settings
from form_designer.utils import JSONFieldDescriptor, get_object


def create_form_submission(model_instance, form_instance, request, **kwargs):
    return FormSubmission.objects.create(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        path=request.path)


def send_as_mail(model_instance, form_instance, request, config, **kwargs):
    submission = FormSubmission(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        path=request.path)

    send_mail(
        model_instance.title,
        submission.formatted_data(),
        django_settings.DEFAULT_FROM_EMAIL,
        [config['email']],
        fail_silently=True)
    return _('Thank you, your input has been received.')


@python_2_unicode_compatible
class Form(models.Model):
    CONFIG_OPTIONS = [
        ('save_fs', {
            'title': _('Save form submission'),
            'process': create_form_submission,
        }),
        ('email', {
            'title': _('Send e-mail'),
            'form_fields': [
                ('email', forms.EmailField(label=_('e-mail address'))),
            ],
            'process': send_as_mail,
        }),
    ]

    title = models.CharField(_('title'), max_length=100)

    config_json = models.TextField(_('config'), blank=True)
    config = JSONFieldDescriptor('config_json')

    class Meta:
        verbose_name = _('form')
        verbose_name_plural = _('forms')

    def __str__(self):
        return self.title

    def form(self):
        fields = OrderedDict((
            ('required_css_class', 'required'),
            ('error_css_class', 'error'),
        ))

        for field in self.fields.all():
            field.add_formfield(fields, self)

        validators = []
        cfg = dict(self.CONFIG_OPTIONS)
        for key, config in self.config.items():
            try:
                validators.append(cfg[key]['validate'])
            except KeyError:
                pass

        class Form(forms.Form):
            def clean(self):
                data = super(Form, self).clean()
                for validator in validators:
                    validator(self, data)
                return data

        return type(str('Form%s' % self.pk), (Form,), fields)

    def process(self, form, request):
        ret = {}
        cfg = dict(self.CONFIG_OPTIONS)

        for key, config in self.config.items():
            try:
                process = cfg[key]['process']
            except KeyError:
                # ignore configs without process methods
                continue

            ret[key] = process(
                model_instance=self,
                form_instance=form,
                request=request,
                config=config)

        return ret


FIELD_TYPES = get_object(settings.FORM_DESIGNER_FIELD_TYPES)


def get_type_choices():
    return [r[:2] for r in
            get_object(settings.FORM_DESIGNER_FIELD_TYPES)]


@python_2_unicode_compatible
class FormField(models.Model):
    form = models.ForeignKey(
        Form, related_name='fields', verbose_name=_('form'),
        on_delete=models.CASCADE)
    ordering = models.IntegerField(_('ordering'), default=0)

    title = models.CharField(_('title'), max_length=100)
    name = models.CharField(_('name'), max_length=100)
    type = models.CharField(
        _('type'), max_length=20, choices=lazy(get_type_choices, list)())
    choices = models.CharField(
        _('choices'), max_length=1024, blank=True,
        help_text=_('Comma-separated'))
    help_text = models.CharField(
        _('help text'), max_length=1024, blank=True,
        help_text=_('Optional extra explanatory text beside the field'))
    default_value = models.CharField(
        _('default value'), max_length=255, blank=True,
        help_text=_('Optional default value of the field'))
    is_required = models.BooleanField(_('is required'), default=True)

    class Meta:
        ordering = ['ordering', 'id']
        unique_together = (('form', 'name'),)
        verbose_name = _('form field')
        verbose_name_plural = _('form fields')

    def __str__(self):
        return self.title

    def clean(self):
        if self.choices and not isinstance(self.get_type(), forms.ChoiceField):
            raise forms.ValidationError(
                _("You can't specify choices for %s fields") % self.type)

    def get_choices(self):
        def get_tuple(value):
            return (slugify(value.strip()), value.strip())

        choices = [get_tuple(value) for value in self.choices.split(',')]
        if not self.is_required and self.type == 'select':
            choices = BLANK_CHOICE_DASH + choices
        return tuple(choices)

    def get_type(self, **kwargs):
        types = dict((r[0], r[2]) for r in FIELD_TYPES)
        return types[self.type](**kwargs)

    def add_formfield(self, fields, form):
        fields[slugify(self.name)] = self.formfield()

    def formfield(self):
        kwargs = dict(
            label=self.title,
            required=self.is_required,
            initial=self.default_value,
        )
        if self.choices:
            kwargs['choices'] = self.get_choices()
        if self.help_text:
            kwargs['help_text'] = self.help_text
        return self.get_type(**kwargs)


class FormSubmission(models.Model):
    submitted = models.DateTimeField(auto_now_add=True)
    form = models.ForeignKey(
        Form, verbose_name=_('form'), related_name='submissions',
        on_delete=models.CASCADE)
    data = models.TextField()
    path = models.CharField(max_length=255)

    class Meta:
        ordering = ('-submitted',)
        verbose_name = _('form submission')
        verbose_name_plural = _('form submissions')

    def sorted_data(self, include=()):
        """ Return OrderedDict by field ordering and using titles as keys.

        `include` can be a tuple containing any or all of 'date', 'time',
        'datetime', or 'path' to include additional meta data.
        """
        data_dict = json.loads(self.data)
        data = OrderedDict()
        field_names = []
        for field in self.form.fields.all():
            data[field.title] = data_dict.get(field.name)
            field_names.append(field.name)
        # append any extra data (form may have changed since submission, etc)
        for field_name in data_dict:
            if field_name not in field_names:
                data[field_name] = data_dict[field_name]
        if 'datetime' in include:
            data['submitted'] = self.submitted
        if 'date' in include:
            data['date submitted'] = self.submitted.date()
        if 'time' in include:
            data['time submitted'] = self.submitted.time()
        if 'path' in include:
            data['form path'] = self.path
        return data

    def formatted_data(self, html=False):
        formatted = ""
        for key, value in self.sorted_data().items():
            if html:
                formatted += format_html(
                    "<dt>{}</dt><dd>{}</dd>\n",
                    key,
                    value,
                )
            else:
                formatted += "%s: %s\n" % (key, value)
        return mark_safe("<dl>%s</dl>" % formatted) if html else formatted

    def formatted_data_html(self):
        return self.formatted_data(html=True)
