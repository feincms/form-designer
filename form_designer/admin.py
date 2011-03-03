import csv
from threading import currentThread

from django import forms
from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf.urls.defaults import patterns, url
from django.db.models import Model
from django.utils import simplejson
from django.utils.text import truncate_words
from django.utils.translation import ugettext_lazy as _

from . import models

import cStringIO
import codecs

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        row = [unicode(s) for s in row]
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# Internal state tracking helper for config fields
_formdesigner_admin_state = {}


def jsonize(v):
    if isinstance(v, dict):
        return dict((i1, jsonize(i2)) for i1, i2 in v.items())
    if hasattr(v, '__iter__'):
        return [jsonize(i) for i in v]
    if isinstance(v, Model):
        return v.pk
    return v


class FormAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'config_json': forms.Textarea(attrs={'rows': 3}),
            }

    def __init__(self, *args, **kwargs):
        super(FormAdminForm, self).__init__(*args, **kwargs)

        choices = ((key, cfg.get('title', key)) for key, cfg in self._meta.model.CONFIG_OPTIONS)

        self.fields['config_options'] = forms.MultipleChoiceField(
            choices=choices,
            label=_('Configuration options'),
            help_text=_('Save and continue editing to configure options.'),
            )

        request = _formdesigner_admin_state[currentThread()]
        request._formdesigner_discount_config_fieldsets = []

        try:
            selected = self.data.getlist('config_options')
        except AttributeError:
            if self.instance.pk:
                selected = self.instance.config.keys()
            else:
                selected = None

        selected = selected or ()
        self.fields['config_options'].initial = selected

        for s in selected:
            cfg = dict(self._meta.model.CONFIG_OPTIONS)[s]

            fieldset = [
                _('Form configuration: %s') % cfg.get('title', s),
                {'fields': []},
                ]

            for k, f in cfg.get('form_fields', []):
                self.fields['%s_%s' % (s, k)] = f
                if k in self.instance.config.get(s, {}):
                    f.initial = self.instance.config[s].get(k)
                fieldset[1]['fields'].append('%s_%s' % (s, k))

            request._formdesigner_discount_config_fieldsets.append(fieldset)

    def clean(self):
        data = self.cleaned_data

        if 'config_json' in self.changed_data:
            return data

        selected = data.get('config_options', [])
        config_options = {}

        for s in selected:
            cfg = dict(self._meta.model.CONFIG_OPTIONS)[s]

            option_item = {}
            for k, f in cfg.get('form_fields', []):
                key = '%s_%s' % (s, k)
                if key in data:
                    option_item[k] = data.get(key)

            config_options[s] = option_item

        data['config_json'] = simplejson.dumps(jsonize(config_options))
        return data


class FormFieldAdmin(admin.TabularInline):
    extra = 1
    model = models.FormField
    prepopulated_fields = {'name': ('title',)}


class FormAdmin(admin.ModelAdmin):
    form = FormAdminForm
    inlines = [FormFieldAdmin]
    list_display = ('title',)
    save_as = True

    def get_form(self, request, obj=None, **kwargs):
        _formdesigner_admin_state[currentThread()] = request
        return super(FormAdmin, self).get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(FormAdmin, self).get_fieldsets(request, obj)
        fieldsets[0][1]['fields'].remove('config_json')

        fieldsets.append((_('Configuration'), {
            'fields': ('config_json', 'config_options'),
            }))

        fieldsets.extend(request._formdesigner_discount_config_fieldsets)
        del _formdesigner_admin_state[currentThread()]

        return fieldsets

    def export_submissions(self, request, form_id):
        form = get_object_or_404(models.Form, pk=form_id)

        rows = []
        for submission in form.submissions.all():
            data = submission.sorted_data(include=('date','time','path'))
            if not rows:
                rows.append(data.keys())
            rows.append([data.get(field_name) for field_name in rows[0]])
            # (fairly gracefully handles changes in form fields between
            #  submissions)

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename=form_submissions.csv'
        writer = UnicodeWriter(response)
        writer.writerows(rows)
        return response

    def get_urls(self):
        return patterns(
            '',
            url(r'(?P<form_id>\d+)/export_submissions/',
                self.admin_site.admin_view(self.export_submissions))
            ) + super(FormAdmin, self).get_urls()


class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('form', 'path', 'submitted', 'data_summary')
    fields = ('form', 'path', 'submitted')
    readonly_fields = fields
    def data_summary(self, submission):
        return truncate_words(submission.formatted_data(), 15)
    def has_add_permission(self, request):
        return False

admin.site.register(models.Form, FormAdmin)
admin.site.register(models.FormSubmission, FormSubmissionAdmin)
