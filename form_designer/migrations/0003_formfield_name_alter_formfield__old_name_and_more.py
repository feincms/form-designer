# Generated by Django 4.0.3 on 2022-05-18 06:16

import re

from django.db import migrations


def forwards(apps, schema_editor):
    FormField = apps.get_model("form_designer", "FormField")
    for instance in FormField.objects.all():
        instance.name = re.sub(
            r"[^-a-z0-9_]+",
            "-",
            instance._old_name.lower(),
        )
        instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("form_designer", "0002_rename_name_formfield__old_name_and_more"),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            migrations.RunPython.noop,
        ),
        migrations.AlterUniqueTogether(
            name="formfield",
            unique_together={("form", "name")},
        ),
    ]
