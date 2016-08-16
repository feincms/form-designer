VERSION = (0, 8, 0)
__version__ = '.'.join(map(str, VERSION))

default_app_config = 'form_designer.apps.FormDesignerConfig'

# Do not use Django settings at module level as recommended
try:
    from django.utils.functional import LazyObject
except ImportError:
    pass
else:
    class LazySettings(LazyObject):
        def _setup(self):
            from form_designer import default_settings
            self._wrapped = Settings(default_settings)

    class Settings(object):
        def __init__(self, settings_module):
            for setting in dir(settings_module):
                if setting == setting.upper():
                    setattr(self, setting, getattr(settings_module, setting))

    settings = LazySettings()
