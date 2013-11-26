from feincms.module.page.models import Page

from form_designer.models import FormContent


Page.register_templates({
    'key': 'base',
    'title': 'base',
    'path': 'base.html',
    'regions': (
        ('main', 'main'),
    ),
})
Page.create_content_type(FormContent)
