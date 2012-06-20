==================================================
Form Designer - a simple form designer for FeinCMS
==================================================


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

By default, form data is sent by e-mail to a freely definable e-mail address
and stored in the database (a CSV export of saved submissions is provided too).
It is possible to add your own actions, but that's not documented yet. These
actions aren't hardcoded -- they can be freely defined for every form defined
through this form designer.


Installing the form designer
============================

It is assumed that you have a working FeinCMS_ installation already.

Install the package using pip_::

    $ pip install form_designer


Setting up the form designer
============================

- Add ``'form_designer'`` to ``INSTALLED_APPS``.
- Run ``./manage.py migrate form_designer`` if you are using South_, or
  ``./manage.py syncdb`` otherwise.
- Go into Django's admin panel and add one or more forms with the fields you
  require. Also select at least one action in the configuration options
  selectbox, most often you'd want to select both the "E-mail" and the
  "Save form submission" option. After saving once, you'll see additional
  fields belonging to the selected configuration options, in this case
  a field for entering an e-mail address where the submission results should
  be sent to.


Include the forms through a FeinCMS content type
================================================

- Create the content type for including forms on CMS pages::

    from feincms.module.page.models import Page
    from form_designer.models import FormContent

    Page.create_content_type(FormContent)

- Create the appropriate migrations for the page module or run
  ``./manage.py syncdb`` if you aren't using South_. (But hey, you really
  should!)

- Add the form to a page.

- Profit!


.. _FeinCMS: http://www.feincms.org/
.. _South: http://south.aeracode.org/
