Change log
==========

Next version
------------

0.20
----

* Added Django 4.1 to the CI matrix.
* Extended the ``email`` action with the optional ability to add the author of
  the sibmission to the Cc: of the sent email.
* Changed mails to prefer the titles of fields instead of their name.
* Included field titles in the XLSX export when possible.
* Removed our usage of ``collections.OrderedDict``, not necessary anymore.
* Changed submissions to save the full URL, not just the path. Cleaned up the
  form submissions model while at it.


0.19
----

* Specified the default ``AutoField`` for the form designer to avoid
  migrations.
* Added a reCAPTCHA v3 field to the default field types.
* Added Django 4.0a1 to the CI matrix.
* Disallowed non-sluggy contents on the name field. The old field name is
  preserved for exporting form submissions etc. so the change *should* be
  backwards compatible but don't rely on it too much.
* Raised the minimum requirements to Python 3.8, Django 3.2.


0.18
----

* Stopped hardcoding the admin base form class. Overriding the ``form``
  attribute on the ``ModelAdmin`` class for forms now works as expected.
* Raised the minimum requirements to Python 3.6, Django 2.2.
* Switched to a declarative setup.
* Switched to GitHub actions.


0.17
----

* Fixed a typo and changed e-mail to email. Removed the help text from
  config options which isn't correct anymore.
* Added code to avoid crashing the admin interface if form submissions
  cannot be deserialized and/or rendered.
* Worked around changes in the initialization of change forms in the
  administration interface.
* Added Django 3.1 and Python 3.8 to the Travis CI matrix.
* Reordered the configuration options in the administration panel; moved
  activation of processors closer to their configuration.
* Fixed a recurring bug where migrations would be created when changing
  field types.
* Made the ordering field a bit wider so that the value is still visible
  even on small screens.


0.16
----

* Fixed the config fieldsets code to work when using Django 3.0.
* Added an unit test and docs for the ``"validate"`` config option.
* Passed additional data to the ``"validate"`` config option. Not
  accepting arbitrary keyword arguments is now deprecated.
* Changed the forms administration interface to show all form options
  from the beginning. This requires a change to the ``form_fields``
  configuration option: Instead of a list it has to be a callable
  accepting the form instance now.
* Added support for specifying a description for config options.


0.15
----

* Restructured the ``FIELD_TYPES`` data structure to use a dictionary
  instead of a tuple to allow for future expansion.
* Dropped compatibility with Python 2.


0.14
----

* Fixed the package to include static files and templates.
* Raised the minimum django-recaptcha version to 2.0.


0.13
----

* Added `tox <https://tox.readthedocs.io/>`__ configuration for easily
  running linters and tests locally.
* Reformatted the project using `black
  <https://black.readthedocs.io/>`__
* Made `django-admin-ordering
  <https://github.com/matthiask/django-admin-ordering/>`__ a dependency.
* Replaced the CSV export with an XLSX export based on `xlsxdocument
  <https://github.com/matthiask/xlsxdocument>`__. It just is a better
  format.
* Improved the test coverage a bit and fixed an edge case where
  form field model validation would crash.


0.12
----

* Changed ``FormSubmission.sorted_data`` (and by extension also
  ``formatted_data(_html)`` and the CSV export) to use field names
  instead of field titles as keys. Field names are guaranteed to be
  unique, titles are not.


0.11
----

* Moved form processing into ``FormContent.process``; this removes the
  need to pass the request to ``FormContent.render``. ``render`` is not
  expected to require a request parameter in FeinCMS content types.
* Added Django 1.11 to the test matrix. No changes were necessary for
  1.11 support.
* Added documentation for adding new actions.
* Fixed a bug where activated config options were lost because of
  differences between ``list()`` and ``dict_keys()`` objects.


0.10
----

* Make the fields tabular inline a bit less wide.
* Added czech translations.
* Fixed the usage of ``render_to_string`` to actually work correctly
  with Django 1.10.


0.9
---

* The form admin uses django-admin-ordering_ for fields if available.
* Now supports sending notification mails to multiple addresses.


0.8
---

* Moved the ``FormContent`` to the new module ``form_designer.contents``
  to make the form designer usable without FeinCMS_.
* Replaced ``SortedDict`` with ``collections.OrderedDict``.
* Fixed an XSS vulnerability in the administration.
* Dropped compatibility with old Django versions (<1.8).
* Replaced the horrible form submission serialization of ``repr()`` and
  ``eval()`` with JSON.
* General packaging and code cleanups.


0.7
---

* Avoid the deprecated ``mimetype`` argument to HTTP responses.
* Fixed infinite recursion in ``jsonize``.
* Made field type choices lazy so that changing available field types is
  easier resp. actually possible.


0.6
---

* Improve code coverage, less warnings, less complaining.


0.5
---

* Added an app config for a nicer app name.


0.4
---

* Built-in support for Django 1.7-style migrations. If you're using South,
  update to South 1.0 or better.


0.3
---

* Support for Python 3.3, 2.7 and 2.6.
* Support for overridding field types with ``FORM_DESIGNER_FIELD_TYPES``.
