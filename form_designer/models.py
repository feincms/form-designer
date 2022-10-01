import json
import warnings
from functools import partial

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import RegexValidator, validate_email
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.html import format_html, format_html_join
from django.utils.inspect import func_accepts_kwargs
from django.utils.module_loading import import_string
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _

from form_designer.utils import JSONFieldDescriptor


def process_save_fs(model_instance, form_instance, request, **kwargs):
    return FormSubmission.objects.create(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        url=request.build_absolute_uri(request.get_full_path()),
    )


def process_email(model_instance, form_instance, request, config, **kwargs):
    submission = FormSubmission(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        url=request.build_absolute_uri(request.get_full_path()),
    )

    recipients = {
        "to": [email.strip() for email in config["email"].split(",")],
    }
    if (author_email_field := config.get("author_email_field")) and (
        email := form_instance.cleaned_data.get(author_email_field)
    ):
        recipients["cc"] = [email]

    EmailMessage(
        model_instance.title,
        submission.formatted_data(titles=submission.titles()),
        **recipients,
    ).send(fail_silently=True)
    return _("Thank you, your input has been received.")


def validate_comma_separated_emails(value):
    for v in value.split(","):
        validate_email(v.strip())


class Form(models.Model):
    CONFIG_OPTIONS = [
        (
            "save_fs",
            {
                "title": _("Save form submission"),
                "description": _(
                    "Save form submissions in the database"
                    " so that they may be exported later."
                ),
                "process": process_save_fs,
            },
        ),
        (
            "email",
            {
                "title": _("Send email"),
                "description": _(
                    "Send the submitted form data to a list of email addresses."
                ),
                "form_fields": lambda form: [
                    (
                        "email",
                        forms.CharField(
                            label=capfirst(_("email address")),
                            validators=[validate_comma_separated_emails],
                            help_text=_(
                                "Separate multiple email addresses with commas."
                            ),
                        ),
                    ),
                    (
                        "author_email_field",
                        forms.EmailField(
                            label=capfirst(_("author's email field")),
                            help_text=_(
                                "The author of the submission will be added to the Cc: if this is set to an existing form field below."
                            ),
                            required=False,
                        ),
                    ),
                ],
                "process": process_email,
            },
        ),
    ]

    title = models.CharField(_("title"), max_length=100)

    config_json = models.TextField(_("config"), blank=True)
    config = JSONFieldDescriptor("config_json")

    class Meta:
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def __str__(self):
        return self.title

    def form_class(self):
        fields = {
            "required_css_class": "required",
            "error_css_class": "error",
        }

        for field in self.fields.all():
            field.add_formfield(fields, self)

        validators = []
        cfg = dict(self.CONFIG_OPTIONS)
        for key, config in self.config.items():
            try:
                validator = cfg[key]["validate"]
            except KeyError:
                pass
            else:
                if func_accepts_kwargs(validator):
                    validator = partial(validator, config=config, model_instance=self)
                else:
                    warnings.warn(
                        f"validate of {key!r} should accept **kwargs",
                        DeprecationWarning,
                    )
                validators.append(validator)

        class Form(forms.Form):
            def clean(self):
                data = super().clean()
                for validator in validators:
                    validator(self, data)
                return data

        return type(str("Form%s" % self.pk), (Form,), fields)

    def form(self):  # pragma: no cover
        warnings.warn("Use form_class instead", DeprecationWarning, stacklevel=2)
        return self.form_class()

    def process(self, form, request):
        ret = {}
        cfg = dict(self.CONFIG_OPTIONS)

        for key, config in self.config.items():
            try:
                process = cfg[key]["process"]
            except KeyError:
                # ignore configs without process methods
                continue

            ret[key] = process(
                model_instance=self, form_instance=form, request=request, config=config
            )

        return ret


FIELD_TYPES = import_string(
    getattr(
        settings,
        "FORM_DESIGNER_FIELD_TYPES",
        "form_designer.default_field_types.FIELD_TYPES",
    )
)
for index, field_type in enumerate(FIELD_TYPES[:]):
    if isinstance(field_type, dict):
        continue
    warnings.warn(
        "Form designer field type %r still uses the old configuration format."
        % (field_type,),
        DeprecationWarning,
    )
    FIELD_TYPES[index] = {
        "type": field_type[0],
        "verbose_name": field_type[1],
        "field": field_type[2],
    }


class _StaticChoicesCharField(models.CharField):
    """Does not detect changes to "choices", ever"""

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["choices"] = [("", "")]
        return name, "django.db.models.CharField", args, kwargs


class NameField(models.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            "validators",
            [
                RegexValidator(
                    r"^[-a-z0-9_]+$",
                    message=_(
                        "Enter a value consisting only of lowercase letters,"
                        " numbers, dashes and the underscore."
                    ),
                ),
            ],
        )
        kwargs.setdefault(
            "help_text",
            _(
                "Data is saved using this name. Changing it may result in data loss."
                " This field only allows a-z, 0-9, - and _ as characters."
            ),
        )
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.CharField", args, kwargs

    def formfield(self, **kwargs):
        kwargs.setdefault("required", False)
        return super().formfield(**kwargs)


class FormField(models.Model):
    form = models.ForeignKey(
        Form, related_name="fields", verbose_name=_("form"), on_delete=models.CASCADE
    )
    ordering = models.IntegerField(_("ordering"), default=0)

    title = models.CharField(_("field title"), max_length=100)
    name = NameField(verbose_name=_("field name"), max_length=100)
    _old_name = models.CharField(editable=False, null=True, max_length=100)
    type = _StaticChoicesCharField(
        _("field type"),
        max_length=20,
        choices=[(type["type"], type["verbose_name"]) for type in FIELD_TYPES],
    )
    choices = models.CharField(
        _("choices"), max_length=1024, blank=True, help_text=_("Comma-separated")
    )
    help_text = models.CharField(
        _("help text"),
        max_length=1024,
        blank=True,
        help_text=_("Optional extra explanatory text beside the field"),
    )
    default_value = models.CharField(
        _("default value"),
        max_length=255,
        blank=True,
        help_text=_("Optional default value of the field"),
    )
    is_required = models.BooleanField(_("is required"), default=True)

    class Meta:
        ordering = ["ordering", "id"]
        unique_together = (("form", "name"),)
        verbose_name = _("form field")
        verbose_name_plural = _("form fields")

    def __str__(self):
        return self.title

    def clean(self):
        try:
            cfg = next(type for type in FIELD_TYPES if type["type"] == self.type)
        except StopIteration:
            # Fine. The model will not validate anyway.
            return

        for fn in cfg.get("clean_field", ()):
            fn(self)

    def get_choices(self):
        def get_tuple(value):
            return (slugify(value.strip()), value.strip())

        choices = [get_tuple(value) for value in self.choices.split(",")]
        if not self.is_required and self.type == "select":
            choices = BLANK_CHOICE_DASH + choices
        return tuple(choices)

    def get_type(self, **kwargs):
        types = {type["type"]: type["field"] for type in FIELD_TYPES}
        return types[self.type](**kwargs)

    def add_formfield(self, fields, form):
        fields[slugify(self.name)] = self.formfield()

    def formfield(self):
        kwargs = dict(
            label=self.title,
            required=self.is_required,
            initial=self.default_value,
            help_text=self.help_text,
        )
        if self.choices:
            kwargs["choices"] = self.get_choices()
            # The value of individual choices is slugified too.
            kwargs["initial"] = slugify(self.default_value)
        return self.get_type(**kwargs)


class FormSubmission(models.Model):
    submitted_at = models.DateTimeField(_("submitted at"), auto_now_add=True)
    form = models.ForeignKey(
        Form,
        verbose_name=_("form"),
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    data = models.TextField(_("data"))
    url = models.CharField(_("URL"), max_length=2000)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = _("form submission")
        verbose_name_plural = _("form submissions")

    def sorted_data(self, include=()):
        """Return dict by field ordering and using names as keys.

        `include` can be a tuple containing any or all of 'meta:date',
        'meta:time', 'meta:datetime', or 'meta:url' to include additional meta
        data.
        """
        data_dict = json.loads(self.data)
        data = {}
        old_names = set()
        for field in self.form.fields.all():
            if field._old_name is not None and field._old_name in data_dict:
                data[field.name] = data_dict.get(field._old_name)
                old_names.add(field._old_name)
            else:
                data[field.name] = data_dict.get(field.name)
        # append any extra data (form may have changed since submission, etc)
        for field_name in data_dict:
            if field_name not in data and field_name not in old_names:
                data[field_name] = data_dict[field_name]
        if "meta:datetime" in include:
            data["meta:datetime"] = self.submitted_at
        if "meta:date" in include:
            data["meta:date"] = self.submitted_at.date()
        if "meta:time" in include:
            data["meta:time"] = self.submitted_at.time()
        if "meta:url" in include:
            data["meta:url"] = self.url
        return data

    def titles(self):
        titles = {
            "meta:datetime": _("submitted"),
            "meta:date": _("date submitted"),
            "meta:time": _("time submitted"),
            "meta:url": _("form URL"),
        }
        titles.update(dict(self.form.fields.values_list("name", "title")))
        return titles

    def formatted_data(self, *, html=False, titles=None, default="Ø"):
        titles = {} if titles is None else titles
        data = (
            (titles.get(key, key), value or default)
            for key, value in self.sorted_data().items()
        )
        if html:
            return format_html(
                "<dl>{}</dl>",
                format_html_join("", "<dt>{}</dt><dd>{}</dd>", data),
            )
        return "\n".join("%s:\n%s\n" % item for item in data)
