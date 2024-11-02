#!/usr/bin/env python3

import os
import sys
import importlib

sys.path.append(os.path.abspath("../../src/"))

with open("../../VERSION", "r") as f:
    pyversion = f.read().strip()


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '3.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx',
              'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.imgmath',
              'sphinx.ext.ifconfig', 'sphinx.ext.viewcode', 'numpydoc', 'myst_parser']

templates_path = ['_templates']

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = "datadigitizer" 
project_copyright = "2024 Milan Skocic"
author = "Milan Skocic"
version = pyversion
release = version

exclude_patterns = []

html_theme = "pydata_sphinx_theme"


latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'preamble': r"""\DeclareUnicodeCharacter{2212}{-}""",
    'figure_align': 'htbp',
}




# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org', None),
                       'numpy': ('https://docs.scipy.org/doc/numpy', None),
                       'scipy': ('https://docs.scipy.org/doc/scipy/reference', None),
                       'matplotlib': ('https://matplotlib.org/stable', None),
                       'sympy': ('https://docs.sympy.org/latest', None)}

numpy_show_class_members = True
numpydoc_show_inherited_class_members = False

autoclass_content = 'init'  # PEP257 indicates that classes should be documented in __init__
