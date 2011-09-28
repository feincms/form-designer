==================================================
Form Designer - a simple form designer for FeinCMS
==================================================

This form designer does not try to offer every last configuration possibility
of Django's forms, just through the administration interface instead of directly
in Python code. Instead, it strives to be a tool which everyone can use right
away, without the need for long explanations.

It offers a small set of predefined input fields such as:

* Text fields (One line and multi line widgets possible)
* E-mail address fields
* Checkboxes
* Dropdowns
* Radio Buttons
* Multiple selection checkboxes

Every field can optionally be declared mandatory, default values and help texts
are available too. That's it.

By default, form data is sent by e-mail to a freely definable e-mail address and
stored in the database (a CSV export of saved submissions is provided too).
It is possible to add your own actions, but that's not documented yet. These
actions aren't hardcoded -- they can be freely defined for every form defined
through this form designer.


Visit these sites for more information
======================================

* form_designer: https://github.com/matthiask/form_designer
* FeinCMS: http://www.feinheit.ch/labs/feincms-django-cms/
