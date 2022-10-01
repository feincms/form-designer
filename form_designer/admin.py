import json
import warnings

from admin_ordering.admin import OrderableAdmin
from django import forms
from django.contrib import admin
from django.db.models import Model
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.urls import re_path
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from xlsxdocument import XLSXDocument

from form_designer import models


def jsonize(v):
    if isinstance(v, dict):
        return {i1: jsonize(i2) for i1, i2 in v.items()}
    if hasattr(v, "__iter__") and not isinstance(v, str):
        return [jsonize(i) for i in v]
    if isinstance(v, Model):
        return v.pk
    return v


class FormAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"config_json": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config_fieldsets = []

        selected = []
        if self.data:
            try:
                selected = [
                    cfg_key
                    for cfg_key, cfg in self._meta.model.CONFIG_OPTIONS
                    if "_is_active_%s" % cfg_key in self.data
                ]
            except KeyError:
                pass

        if not selected and self.instance.pk:
            selected = self.instance.config.keys()

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

            self.fields["_is_active_%s" % cfg_key] = forms.BooleanField(
                label=capfirst(_("is active")),
                required=False,
                initial=cfg_key in selected,
            )

            for k, f in self._form_fields(cfg_key, cfg):
                self.fields[f"{cfg_key}_{k}"] = f
                if k in self.instance.config.get(cfg_key, {}):
                    f.initial = self.instance.config[cfg_key].get(k)
                fieldset[1]["fields"].append(f"{cfg_key}_{k}")
                if is_optional:
                    f.required = False

            config_fieldsets.append(fieldset)

        self.request._formdesigner_config_fieldsets = config_fieldsets

    def clean(self):
        data = self.cleaned_data

        if "config_json" in self.changed_data:
            return data

        selected = [
            cfg_key
            for cfg_key, cfg in self._meta.model.CONFIG_OPTIONS
            if "_is_active_%s" % cfg_key in self.data
        ]
        config = {}

        for s in selected:
            cfg = dict(self._meta.model.CONFIG_OPTIONS)[s]

            option_item = {}
            for k, _f in self._form_fields(s, cfg):
                key = f"{s}_{k}"
                if key in data:
                    option_item[k] = data.get(key)

            config[s] = option_item

        data["config_json"] = json.dumps(jsonize(config))
        return data

    def _form_fields(self, cfg_key, cfg):
        form_fields = cfg.get("form_fields")
        if not form_fields:
            return []
        if callable(form_fields):
            return form_fields(self)  # TODO arguments?
        warnings.warn(
            f"form_fields of {cfg_key!r} should be a callable",
            DeprecationWarning,
        )
        return form_fields


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
        if not hasattr(request, "_formdesigner_form_class"):
            # Generate a new class with the _current_ request as a class variable
            # form_class = super(FormAdmin, self).get_form(request, obj, **kwargs)
            form_class = modelform_factory(self.model, form=self.form, fields="__all__")
            request._formdesigner_form_class = type(
                self.form.__name__,
                (form_class,),
                {"request": request},
            )
        return request._formdesigner_form_class

    def _form_fields(self, cfg_key, cfg):
        form_fields = cfg.get("form_fields")
        if not form_fields:
            return []
        if callable(form_fields):
            return form_fields(None)  # TODO arguments?
        warnings.warn(
            f"form_fields of {cfg_key!r} should be a callable",
            DeprecationWarning,
        )
        return form_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {"fields": ["title"]}),
        ]

        for cfg_key, cfg in self.model.CONFIG_OPTIONS:
            fields = ["_is_active_%s" % cfg_key]
            fields.extend(
                f"{cfg_key}_{row[0]}" for row in self._form_fields(cfg_key, cfg)
            )
            fieldsets.append(
                (
                    _("Form configuration: %s") % cfg.get("title", cfg_key),
                    {
                        "fields": fields,
                        "classes": ["form-designer"],
                        "description": cfg.get("description"),
                    },
                ),
            )

        fieldsets.append(
            (_("Configuration"), {"fields": ["config_json"], "classes": ["collapse"]}),
        )
        return fieldsets

    def export_submissions(self, request, form_id):
        form = get_object_or_404(models.Form, pk=form_id)

        rows = []
        field_names = None
        for submission in form.submissions.all():
            data = submission.sorted_data(
                include=("meta:date", "meta:time", "meta:url")
            )
            if field_names is None:
                field_names = list(data.keys())
                titles = submission.titles()
                rows.append([titles.get(name, name) for name in field_names])
                rows.append(field_names)
            rows.append([data.get(name) for name in field_names])
            # (fairly gracefully handles changes in form fields between
            #  submissions)

        xlsx = XLSXDocument()
        xlsx.add_sheet(slugify(form.title))
        xlsx.table([], rows)
        return xlsx.to_response("%s.xlsx" % slugify(form.title))

    def get_urls(self):
        return [
            re_path(
                r"(?P<form_id>\d+)/export_submissions/",
                self.admin_site.admin_view(self.export_submissions),
                name="form_designer_formsubmission_export",
            )
        ] + super().get_urls()


class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ["form", "url", "submitted_at", "data_summary"]
    list_filter = ["form"]
    fields = ["form", "url", "submitted_at"]
    readonly_fields = fields

    def data_summary(self, submission):
        data = submission.formatted_data()
        if len(data) > 100:
            return "%s..." % data[:95]
        return data

    def has_add_permission(self, request):
        return False

    def render_change_form(self, request, context, **kwargs):
        if obj := kwargs.get("obj"):
            try:
                context["formatted_data"] = obj.formatted_data(
                    html=True, titles=obj.titles()
                )
            except Exception:
                context["formatted_data"] = f"BROKEN: {obj.data}"
        return super().render_change_form(request, context, **kwargs)


admin.site.register(models.Form, FormAdmin)
admin.site.register(models.FormSubmission, FormSubmissionAdmin)
