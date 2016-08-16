from __future__ import unicode_literals

from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline

from form_designer.models import Form


class FormContentInline(FeinCMSInline):
    raw_id_fields = ('form',)


class FormContent(models.Model):
    feincms_item_editor_inline = FormContentInline

    form = models.ForeignKey(Form, verbose_name=_('form'),
                             related_name='%(app_label)s_%(class)s_related',
                             on_delete=models.CASCADE)
    show_form_title = models.BooleanField(_('show form title'), default=True)
    success_message = models.TextField(
        _('success message'),
        help_text=_("Custom message to display after valid form is submitted"))

    template = 'content/form/form.html'

    class Meta:
        abstract = True
        verbose_name = _('form')
        verbose_name_plural = _('forms')

    def process_valid_form(self, request, form_instance, **kwargs):
        """ Process form and return response (hook method). """
        process_result = self.form.process(form_instance, request)
        context = RequestContext(
            request,
            {
                'content': self,
                'message': self.success_message or process_result or u'',
            }
        )
        return render_to_string(self.template, context)

    def render(self, request, **kwargs):
        form_class = self.form.form()
        prefix = 'fc%d' % self.id
        formcontent = request.POST.get('_formcontent')

        if request.method == 'POST' and (
                not formcontent or formcontent == smart_text(self.id)):
            form_instance = form_class(request.POST, prefix=prefix)

            if form_instance.is_valid():
                return self.process_valid_form(
                    request, form_instance, **kwargs)
        else:
            form_instance = form_class(prefix=prefix)

        context = RequestContext(
            request, {'content': self, 'form': form_instance})
        return render_to_string(self.template, context)
