from __future__ import unicode_literals

import os
import sys


sys.path.append(os.path.abspath(".."))

extensions = []

templates_path = ["_templates"]

source_suffix = ".rst"

master_doc = "index"

project = "form-designer"
copyright = "2010 - 2017 Feinheit AG"

version = __import__("form_designer").__version__
release = version

pygments_style = "sphinx"

html_theme = "alabaster"

html_static_path = ["_static"]

htmlhelp_basename = "formdesignerdoc"

latex_documents = [
    (
        "index",
        "formdesigner.tex",
        "form-designer Documentation",
        "Feinheit AG",
        "manual",
    )
]

man_pages = [
    (
        "index",
        "formdesigner",
        "form-designer Documentation",
        ["Feinheit AG"],
        1,
    )
]

texinfo_documents = [
    (
        "index",
        "formdesigner",
        "form-designer Documentation",
        "Feinheit AG",
        "formdesigner",
        "A simple form designer for Django",
        "Miscellaneous",
    )
]
