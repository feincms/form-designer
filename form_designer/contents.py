from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.translation import gettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline

from form_designer.models import Form


class FormContentInline(FeinCMSInline):
    raw_id_fields = ("form",)


class FormContent(models.Model):
    feincms_item_editor_inline = FormContentInline

    form = models.ForeignKey(
        Form,
        verbose_name=_("form"),
        related_name="%(app_label)s_%(class)s_related",
        on_delete=models.CASCADE,
    )
    show_form_title = models.BooleanField(_("show form title"), default=True)
    success_message = models.TextField(
        _("success message"),
        help_text=_("Custom message to display after valid form is submitted"),
    )

    template = "content/form/form.html"

    class Meta:
        abstract = True
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def process_valid_form(self, request, form_instance, **kwargs):
        """ Process form and return response (hook method). """
        process_result = self.form.process(form_instance, request)
        return render_to_string(
            self.template,
            {"content": self, "message": self.success_message or process_result or ""},
            request=request,
        )

    def process(self, request, **kwargs):
        self.request = request

        form_class = self.form.form_class()
        prefix = "fc%d" % self.id
        formcontent = self.request.POST.get("_formcontent")

        if self.request.method == "POST" and (
            not formcontent or formcontent == smart_text(self.id)
        ):
            form_instance = form_class(self.request.POST, prefix=prefix)

            if form_instance.is_valid():
                self._rendered_content = self.process_valid_form(
                    self.request, form_instance, **kwargs
                )
                return
        else:
            form_instance = form_class(prefix=prefix)

        self._rendered_content = render_to_string(
            self.template,
            {"content": self, "form": form_instance},
            request=self.request,
        )

    def render(self, **kwargs):
        return getattr(self, "_rendered_content", "")
