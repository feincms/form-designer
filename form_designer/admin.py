import json
import six
import warnings

from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.db.models import Model
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from admin_ordering.admin import OrderableAdmin
from form_designer import models
from xlsxdocument import XLSXDocument


def jsonize(v):
    if isinstance(v, dict):
        return dict((i1, jsonize(i2)) for i1, i2 in v.items())
    if hasattr(v, "__iter__") and not isinstance(v, six.string_types):
        return [jsonize(i) for i in v]
    if isinstance(v, Model):
        return v.pk
    return v


class FormAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"config_json": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super(FormAdminForm, self).__init__(*args, **kwargs)

        choices = (
            (cfg_key, cfg.get("title", cfg_key))
            for cfg_key, cfg in self._meta.model.CONFIG_OPTIONS
        )

        self.fields["config_options"] = forms.MultipleChoiceField(
            choices=choices, label=_("Options"), widget=forms.CheckboxSelectMultiple,
        )

        config_fieldsets = []

        selected = []
        if self.data:
            try:
                selected = self.data.getlist("config_options", ())
            except AttributeError:
                pass

        if not selected and self.instance.pk:
            selected = self.instance.config.keys()

        self.fields["config_options"].initial = list(selected)

        for cfg_key, cfg in self._meta.model.CONFIG_OPTIONS:
            is_optional = cfg_key not in selected

            fieldset = [
                _("Form configuration: %s") % cfg.get("title", cfg_key),
                {
                    "fields": [],
                    "classes": ("form-designer",),
                    "description": cfg.get("description"),
                },
            ]

            for k, f in self._form_fields(cfg_key, cfg):
                self.fields["%s_%s" % (cfg_key, k)] = f
                if k in self.instance.config.get(cfg_key, {}):
                    f.initial = self.instance.config[cfg_key].get(k)
                fieldset[1]["fields"].append("%s_%s" % (cfg_key, k))
                if is_optional:
                    f.required = False

            config_fieldsets.append(fieldset)

        self.request._formdesigner_config_fieldsets = config_fieldsets

    def clean(self):
        data = self.cleaned_data

        if "config_json" in self.changed_data:
            return data

        selected = data.get("config_options", [])
        config_options = {}

        for s in selected:
            cfg = dict(self._meta.model.CONFIG_OPTIONS)[s]

            option_item = {}
            for k, f in self._form_fields(s, cfg):
                key = "%s_%s" % (s, k)
                if key in data:
                    option_item[k] = data.get(key)

            config_options[s] = option_item

        data["config_json"] = json.dumps(jsonize(config_options))
        return data

    def _form_fields(self, cfg_key, cfg):
        form_fields = cfg.get("form_fields")
        if not form_fields:
            return []
        if callable(form_fields):
            return form_fields(self)  # TODO arguments?
        warnings.warn(
            "form_fields of %r should be a callable" % (cfg_key,), DeprecationWarning,
        )
        return form_fields() if callable(form_fields) else form_fields


class FormFieldAdmin(OrderableAdmin, admin.TabularInline):
    extra = 0
    model = models.FormField
    prepopulated_fields = {"name": ("title",)}
    fk_name = "form"
    ordering_field = "ordering"


class FormAdmin(admin.ModelAdmin):
    form = FormAdminForm
    inlines = [FormFieldAdmin]
    list_display = ("title",)
    save_as = True

    class Media:
        css = {"all": ("form_designer/admin.css",)}

    def get_form(self, request, obj=None, **kwargs):
        form_class = super(FormAdmin, self).get_form(request, obj, **kwargs)
        # Generate a new type to be sure that the request stays inside this
        # request/response cycle.
        return type(form_class.__name__, (form_class,), {"request": request})

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(FormAdmin, self).get_fieldsets(request, obj)
        if not hasattr(request, "_formdesigner_config_fieldsets"):
            return fieldsets

        fieldsets[0][1]["fields"].remove("config_json")

        fieldsets.append(
            (_("Configuration"), {"fields": ("config_json", "config_options")})
        )

        fieldsets.extend(request._formdesigner_config_fieldsets)

        return fieldsets

    def export_submissions(self, request, form_id):
        form = get_object_or_404(models.Form, pk=form_id)

        rows = []
        for submission in form.submissions.all():
            data = submission.sorted_data(include=("date", "time", "path"))
            if not rows:
                rows.append(list(data.keys()))
            rows.append([data.get(field_name) for field_name in rows[0]])
            # (fairly gracefully handles changes in form fields between
            #  submissions)

        xlsx = XLSXDocument()
        xlsx.add_sheet(slugify(form.title))
        xlsx.table([], rows)
        return xlsx.to_response("%s.xlsx" % slugify(form.title))

    def get_urls(self):
        return [
            url(
                r"(?P<form_id>\d+)/export_submissions/",
                self.admin_site.admin_view(self.export_submissions),
                name="form_designer_formsubmission_export",
            )
        ] + super(FormAdmin, self).get_urls()


class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("form", "path", "submitted", "data_summary")
    list_filter = ("form",)
    fields = ("form", "path", "submitted")
    readonly_fields = fields

    def data_summary(self, submission):
        data = submission.formatted_data()
        if len(data) > 100:
            return "%s..." % data[:95]
        return data

    def has_add_permission(self, request):
        return False


admin.site.register(models.Form, FormAdmin)
admin.site.register(models.FormSubmission, FormSubmissionAdmin)
