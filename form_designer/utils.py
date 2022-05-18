import json
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder


class JSONFieldDescriptor:
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, objtype):
        cache_field = "_cached_jsonfield_%s" % self.field
        if not hasattr(obj, cache_field):
            try:
                setattr(
                    obj,
                    cache_field,
                    json.loads(getattr(obj, self.field), parse_float=Decimal),
                )
            except (TypeError, ValueError):
                setattr(obj, cache_field, {})
        return getattr(obj, cache_field)

    def __set__(self, obj, value):
        setattr(obj, "_cached_jsonfield_%s" % self.field, value)
        setattr(obj, self.field, json.dumps(value, cls=DjangoJSONEncoder))
