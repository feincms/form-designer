from decimal import Decimal
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import six
try:
    from importlib import import_module
except ImportError:  # pragma: no cover
    from django.utils.importlib import import_module


class JSONFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, objtype):
        cache_field = '_cached_jsonfield_%s' % self.field
        if not hasattr(obj, cache_field):
            try:
                setattr(
                    obj,
                    cache_field,
                    json.loads(
                        getattr(obj, self.field),
                        parse_float=Decimal,
                    )
                )
            except (TypeError, ValueError):
                setattr(obj, cache_field, {})
        return getattr(obj, cache_field)

    def __set__(self, obj, value):
        setattr(obj, '_cached_jsonfield_%s' % self.field, value)
        setattr(obj, self.field, json.dumps(value, cls=DjangoJSONEncoder))


def get_object(path, fail_silently=False):
    # Return early if path isn't a string (might already be an callable or
    # a class or whatever)
    if not isinstance(path, six.string_types):  # XXX bytes?
        return path

    try:
        return import_module(path)
    except ImportError:
        try:
            dot = path.rindex('.')
            mod, fn = path[:dot], path[dot + 1:]

            return getattr(import_module(mod), fn)
        except (AttributeError, ImportError):
            if not fail_silently:
                raise
