=================================================
Form Designer - a simple form designer for Django
=================================================

.. image:: https://github.com/feincms/form_designer/workflows/Tests/badge.svg
    :target: https://github.com/feincms/form_designer

This form designer does not try to offer every last configuration possibility
of Django's forms, just through the administration interface instead of
directly in Python code. Instead, it strives to be a tool which everyone can
use right away, without the need for long explanations.

It offers a small set of predefined input fields such as:

* Text fields (One line and multi line widgets possible)
* E-mail address fields
* Checkboxes
* Dropdowns
* Radio Buttons
* Multiple selection checkboxes
* Hidden input fields

Every field can optionally be declared mandatory, default values and help texts
are available too. That's it.

The default actions (which can be enabled individually) are to send the form
data to a list of freely definable email addresses and to store the data in the
database so that it can be exported later. An XLSX export of saved submissions
is provided too. It is possible to add your own actions as well.


Installing the form designer
============================

Install the package using pip::

    $ pip install form-designer

Setting up the form designer
============================

- Add ``"form_designer"`` and ``"admin_ordering"`` to ``INSTALLED_APPS``.
- Run ``./manage.py migrate form_designer``
- Go into Django's admin panel and add one or more forms with the fields you
  require. Also select at least one action in the configuration options
  selectbox, most often you'd want to select both the "E-mail" and the
  "Save form submission" option and fill in one ore more email addresses.

If you're using the form designer with FeinCMS_, the content type can be
imported from ``form_designer.contents.FormContent``. Otherwise, your
code should use the following methods (the code would probably reside in
a view):

.. code-block:: python

    # Somehow fetch the form_designer.models.Form instance:
    instance = get_object_or_404()

    # Build the form class:
    form_class = instance.form_class()

    # Standard form processing:
    if request.method == "POST":
        form = form_class(request.POST)

        if form.is_valid():
            # Do what you want, or run the configured processors:
            result = instance.process(form, request)

            # Maybe there's something useful in here:
            pprint(result)

            return HttpResponseRedirect("thanks/")
    else:
        form = form_class()

    return render(request, "form.html", {"form": form})


Adding custom actions
=====================

Custom actions can be added by appending them to
``Form.CONFIG_OPTIONS``:

.. code-block:: python

    from form_designer.models import Form

    def do_thing(model_instance, form_instance, request, config, **kwargs):
        pass

    def do_validate(form_instance, data):
        pass

    Form.CONFIG_OPTIONS.append(
        (
            "do_thing",
            {
                "title": _("Do a thing"),
                "form_fields": lambda form: [
                    ("optional_form_field", forms.CharField(
                        label=_("Optional form field"),
                        required=False,
                        # validators...
                        # help_text...
                    )),
                ],
                "process": do_thing,
                "validate": do_validate,
            },
        )
    )

The interesting part is the ``do_thing`` callable. It currently receives
four arguments, however you should also accept ``**kwargs`` to support
additional arguments added in the future:

- ``model_instance``: The ``Form`` model instance
- ``form_instance``: The dynamically generated form instance
- ``request``: The current HTTP request
- ``config``: The config options (keys and values defined through
  ``form_fields``; for example the ``email`` action defines an ``email``
  char field, and accesses its value using ``config["email"]``.


ReCaptcha
=========

To enable [ReCaptcha](http://www.google.com/recaptcha) install
[django-recaptcha](https://github.com/praekelt/django-recaptcha) and add
`captcha` to your `INSTALLED_APPS`. This will automatically add a ReCaptcha
field to the form designer. For everything else read through the
django-recaptcha readme.


Override field types
====================

Define ``FORM_DESIGNER_FIELD_TYPES`` in your settings file like:

.. code-block:: python

    FORM_DESIGNER_FIELD_TYPES = "your_project.form_designer_config.FIELD_TYPES"

In ``your_project.form_designer_config.py`` something like:

.. code-block:: python

    from django import forms
    from django.utils.translation import gettext_lazy as _

    FIELD_TYPES = [
        {"type": "text", "verbose_name": _("text"), "field": forms.CharField},
        {"type": "email", "verbose_name": _("email address"), "field": forms.EmailField},
    ]


Visit these sites for more information
======================================

* form_designer: https://github.com/feincms/form_designer
* FeinCMS: http://www.feinheit.ch/labs/feincms-django-cms/
* feincms3: https://feincms3.readthedocs.io/

.. _django-admin-ordering: https://github.com/matthiask/django-admin-ordering
.. _FeinCMS: https://feincms-django-cms.readthedocs.io/
