# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('../../src/pynwb'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ndx-hed'
copyright = '2025, Kay Robbins, Ryan Ly, Oliver Ruebel, Ian Callanan'
author = 'Kay Robbins, Ryan Ly, Oliver Ruebel, Ian Callanan'

version = '0.2.0'
release = '0.2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.ifconfig',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'myst_parser',
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autosummary settings
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_favicon = None  # Disable favicon to avoid 404 warnings

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}


############################################################################
#  CUSTOM CONFIGURATIONS ADDED BY THE NWB TOOL FOR GENERATING FORMAT DOCS
###########################################################################

import textwrap  # noqa: E402

# -- Options for intersphinx  ---------------------------------------------
intersphinx_mapping.update({
    'core': ('https://nwb-schema.readthedocs.io/en/latest/', None),
    'hdmf-common': ('https://hdmf-common-schema.readthedocs.io/en/latest/', None),
    'pynwb': ('https://pynwb.readthedocs.io/en/stable/', None),
    'hdmf': ('https://hdmf.readthedocs.io/en/stable/', None),
    'hed': ('https://hed-python.readthedocs.io/en/latest/', None),
})

# -- Generate sources from YAML---------------------------------------------------
# Always rebuild the source docs from YAML even if the folder with the source files already exists
spec_doc_rebuild_always = True


def run_doc_autogen(_):
    # Execute the autogeneration of Sphinx format docs from the YAML sources
    import sys
    import os
    conf_file_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(conf_file_dir)  # Need so that generate format docs can find the conf_doc_autogen file
    from conf_doc_autogen import spec_output_dir

    if spec_doc_rebuild_always or not os.path.exists(spec_output_dir):
        sys.path.append('./docs')  # needed to enable import of generate_format docs
        from hdmf_docutils.generate_format_docs import main as generate_docs
        generate_docs()


def setup(app):
    app.connect('builder-inited', run_doc_autogen)
    # overrides for wide tables in RTD theme
    try:
        app.add_css_file("theme_overrides.css")  # Used by newer Sphinx versions
    except AttributeError:
        app.add_stylesheet("theme_overrides.css")  # Used by older version of Sphinx

# -- Customize sphinx settings
numfig = True
autoclass_content = 'both'
autodoc_docstring_signature = True
autodoc_member_order = 'bysource'
add_function_parentheses = False


# -- HTML sphinx options
html_theme = "sphinx_rtd_theme"
html_favicon = None  # Disable favicon to avoid 404 warnings

# LaTeX Sphinx options
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    'preamble': textwrap.dedent(
        '''
        \\setcounter{tocdepth}{3}
        \\setcounter{secnumdepth}{6}
        \\usepackage{enumitem}
        \\setlistdepth{100}
        '''),
}
