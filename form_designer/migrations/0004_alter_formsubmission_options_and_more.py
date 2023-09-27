# Generated by Django 4.1.1 on 2022-10-01 07:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form_designer", "0003_formfield_name_alter_formfield__old_name_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="formsubmission",
            options={
                "ordering": ["-submitted_at"],
                "verbose_name": "form submission",
                "verbose_name_plural": "form submissions",
            },
        ),
        migrations.RenameField("formsubmission", "submitted", "submitted_at"),
        migrations.RenameField("formsubmission", "path", "url"),
        migrations.AlterField(
            model_name="formsubmission",
            name="submitted_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="submitted at"),
        ),
        migrations.AlterField(
            model_name="formsubmission",
            name="data",
            field=models.TextField(verbose_name="data"),
        ),
        migrations.AlterField(
            model_name="formsubmission",
            name="url",
            field=models.CharField(max_length=2000, verbose_name="URL"),
        ),
    ]
