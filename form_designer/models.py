from collections import OrderedDict
from functools import partial
import json
import warnings

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import validate_email
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.html import format_html, format_html_join
from django.utils.inspect import func_accepts_kwargs
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from form_designer.utils import JSONFieldDescriptor


def create_form_submission(model_instance, form_instance, request, **kwargs):
    return FormSubmission.objects.create(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        path=request.path,
    )


def send_as_mail(model_instance, form_instance, request, config, **kwargs):
    submission = FormSubmission(
        form=model_instance,
        data=json.dumps(form_instance.cleaned_data, cls=DjangoJSONEncoder),
        path=request.path,
    )

    EmailMessage(
        model_instance.title,
        submission.formatted_data(),
        to=[email.strip() for email in config["email"].split(",")],
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
                "process": create_form_submission,
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
                            label=_("email address"),
                            validators=[validate_comma_separated_emails],
                            help_text=_(
                                "Separate multiple email addresses with commas."
                            ),
                        ),
                    )
                ],
                "process": send_as_mail,
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
        fields = OrderedDict(
            (("required_css_class", "required"), ("error_css_class", "error"))
        )

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
                        "validate of %r should accept **kwargs" % (key,),
                        DeprecationWarning,
                    )
                validators.append(validator)

        class Form(forms.Form):
            def clean(self):
                data = super(Form, self).clean()
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


class FormField(models.Model):
    form = models.ForeignKey(
        Form, related_name="fields", verbose_name=_("form"), on_delete=models.CASCADE
    )
    ordering = models.IntegerField(_("ordering"), default=0)

    title = models.CharField(_("field title"), max_length=100)
    name = models.CharField(_("field name"), max_length=100)
    type = models.CharField(
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
            cfg = next((type for type in FIELD_TYPES if type["type"] == self.type))
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
        return self.get_type(**kwargs)


class FormSubmission(models.Model):
    submitted = models.DateTimeField(auto_now_add=True)
    form = models.ForeignKey(
        Form,
        verbose_name=_("form"),
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    data = models.TextField()
    path = models.CharField(max_length=255)

    class Meta:
        ordering = ("-submitted",)
        verbose_name = _("form submission")
        verbose_name_plural = _("form submissions")

    def sorted_data(self, include=()):
        """ Return OrderedDict by field ordering and using names as keys.

        `include` can be a tuple containing any or all of 'date', 'time',
        'datetime', or 'path' to include additional meta data.
        """
        data_dict = json.loads(self.data)
        data = OrderedDict()
        for field in self.form.fields.all():
            data[field.name] = data_dict.get(field.name)
        # append any extra data (form may have changed since submission, etc)
        for field_name in data_dict:
            if field_name not in data:
                data[field_name] = data_dict[field_name]
        if "datetime" in include:
            data["submitted"] = self.submitted
        if "date" in include:
            data["date submitted"] = self.submitted.date()
        if "time" in include:
            data["time submitted"] = self.submitted.time()
        if "path" in include:
            data["form path"] = self.path
        return data

    def formatted_data(self, html=False):
        if html:
            return format_html(
                "<dl>{}</dl>",
                format_html_join(
                    "", "<dt>{}</dt><dd>{}</dd>", self.sorted_data().items()
                ),
            )
        return "".join("%s: %s\n" % item for item in self.sorted_data().items())

    def formatted_data_html(self):
        try:
            return self.formatted_data(html=True)
        except Exception:
            return "BROKEN: %s" % self.data
