# -*- coding: utf-8 -*-
from django.db import models, migrations


field_types = [
    ("text", "text"),
    ("email", "email address"),
    ("longtext", "long text"),
    ("checkbox", "checkbox"),
    ("select", "select"),
    ("radio", "radio"),
    ("multiple-select", "multiple select"),
    ("hidden", "hidden"),
]
try:
    from form_designer.models import FIELD_TYPES

    field_types = [type[:2] for type in FIELD_TYPES]
except Exception:
    pass


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Form",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("title", models.CharField(verbose_name="title", max_length=100)),
                ("config_json", models.TextField(verbose_name="config", blank=True)),
            ],
            options={"verbose_name": "form", "verbose_name_plural": "forms"},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FormField",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("ordering", models.IntegerField(default=0, verbose_name="ordering")),
                ("title", models.CharField(verbose_name="field title", max_length=100)),
                ("name", models.CharField(verbose_name="field name", max_length=100)),
                (
                    "type",
                    models.CharField(
                        verbose_name="field type", choices=field_types, max_length=20
                    ),
                ),
                (
                    "choices",
                    models.CharField(
                        verbose_name="choices",
                        help_text="Comma-separated",
                        blank=True,
                        max_length=1024,
                    ),
                ),
                (
                    "help_text",
                    models.CharField(
                        verbose_name="help text",
                        help_text="Optional extra explanatory text beside the field",
                        blank=True,
                        max_length=1024,
                    ),
                ),
                (
                    "default_value",
                    models.CharField(
                        verbose_name="default value",
                        help_text="Optional default value of the field",
                        blank=True,
                        max_length=255,
                    ),
                ),
                (
                    "is_required",
                    models.BooleanField(default=True, verbose_name="is required"),
                ),
                (
                    "form",
                    models.ForeignKey(
                        related_name="fields",
                        verbose_name="form",
                        to="form_designer.Form",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["ordering", "id"],
                "verbose_name": "form field",
                "verbose_name_plural": "form fields",
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="formfield", unique_together=set([("form", "name")])
        ),
        migrations.CreateModel(
            name="FormSubmission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("submitted", models.DateTimeField(auto_now_add=True)),
                ("data", models.TextField()),
                ("path", models.CharField(max_length=255)),
                (
                    "form",
                    models.ForeignKey(
                        related_name="submissions",
                        verbose_name="form",
                        to="form_designer.Form",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ("-submitted",),
                "verbose_name": "form submission",
                "verbose_name_plural": "form submissions",
            },
            bases=(models.Model,),
        ),
    ]
