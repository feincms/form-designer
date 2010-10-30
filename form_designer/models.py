from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _

from form_designer.utils import JSONFieldDescriptor


class Form(models.Model):
    CONFIG_OPTIONS = [
        ('email', {
            'title': _('E-mail'),
            'form_fields': [
                ('email', forms.EmailField(_('e-mail address'))),
            ],
        }),
    ]

    title = models.CharField(_('title'), max_length=100)

    config_json = models.TextField(_('config'), blank=True)
    config = JSONFieldDescriptor('config_json')

    class Meta:
        verbose_name = _('form')
        verbose_name_plural = _('forms')

    def __unicode__(self):
        return self.title

    def form(self):
        fields = SortedDict()

        for field in self.fields.all():
            field.add_formfield(fields, self)

        return type('Form%s' % self.pk, (forms.Form,), fields)

    def process(self, form, request):
        submission = FormSubmission.objects.create(
            form=self, data=repr(form.cleaned_data), path=request.path)
        
        if 'email' in self.config:
            send_mail(self.title, submission.formatted_data(),
                      settings.DEFAULT_FROM_EMAIL,
                      [self.config['email']['email']], fail_silently=True)
            return _('Thank you, your input has been received.')
        

class FormField(models.Model):
    FIELD_TYPES = [
        ('text', _('text'), forms.CharField),
        ('email', _('e-mail address'), forms.EmailField),
        ('longtext', _('long text'), curry(forms.CharField, widget=forms.Textarea)),
        ('checkbox', _('checkbox'), curry(forms.BooleanField, required=False)),
    ]

    form = models.ForeignKey(Form, related_name='fields',
        verbose_name=_('form'))
    ordering = models.IntegerField(_('ordering'), default=0)

    title = models.CharField(_('title'), max_length=100)
    name = models.CharField(_('name'), max_length=100)
    type = models.CharField(_('type'), max_length=20, choices=[r[:2] for r in FIELD_TYPES])

    is_required = models.BooleanField(_('is required'), default=True)

    class Meta:
        ordering = ['ordering', 'id']
        unique_together = (('form', 'name'),)
        verbose_name = _('form field')
        verbose_name_plural = _('form fields')

    def __unicode__(self):
        return self.title

    def add_formfield(self, fields, form):
        fields[self.name] = self.formfield()

    def formfield(self):
        types = dict((r[0], r[2]) for r in self.FIELD_TYPES)

        return types[self.type](label=self.title, required=self.is_required)


class FormSubmission(models.Model):
    submitted = models.DateTimeField(auto_now_add=True)
    form = models.ForeignKey(Form, verbose_name=_('form'))
    data = models.TextField()
    path = models.CharField(max_length=255)

    class Meta:
        ordering = ('-submitted',)

    def formatted_data(self, html=False):
        formatted = ""
        for key, value in eval(self.data).items():
            if html:
                formatted += "<dt>%s</dt><dd>%s</dd>\n" % (key, value)
            else:
                formatted += "%s: %s\n" % (key, value)
        return formatted if not html else "<dl>%s</dl>" % formatted

    def formatted_data_html(self):
        return self.formatted_data(html=True)
        

class FormContent(models.Model):
    form = models.ForeignKey(Form, verbose_name=_('form'))

    class Meta:
        abstract = True
        verbose_name = _('form content')
        verbose_name_plural = _('form contents')

    def render(self, request, **kwargs):
        form_class = self.form.form()
        prefix = 'fc%d' % self.id

        if request.method == 'POST':
            form_instance = form_class(request.POST, prefix=prefix)

            if form_instance.is_valid():
                return self.form.process(form_instance, request) or u''
        else:
            form_instance = form_class(prefix=prefix)

        context = RequestContext(
            request, {'content': self, 'form': form_instance})
        return render_to_string('content/form/form.html', context)
