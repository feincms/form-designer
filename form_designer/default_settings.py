from django.conf import settings


FORM_DESIGNER_FIELD_TYPES = getattr(
    settings,
    'FORM_DESIGNER_FIELD_TYPES',
    'form_designer.default_field_types.FIELD_TYPES'
)
