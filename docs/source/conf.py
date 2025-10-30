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
    'sphinx_design',
    'sphinx_copybutton',
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

# MyST configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
    "attrs_inline",
]
myst_heading_anchors = 4

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_title = 'ndx-hed: NWB Extension for HED Integration'
html_static_path = ['_static']
html_favicon = None  # Disable favicon to avoid 404 warnings

# Modern theme configuration
html_theme_options = {
    'repository_url': 'https://github.com/hed-standard/ndx-hed',
    'use_repository_button': True,
    'use_issues_button': True,
    'use_edit_page_button': True,
    'path_to_docs': 'docs/source',
    'show_toc_level': 2,
    'navigation_with_keys': False,
    'show_navbar_depth': 1,
    'use_download_button': True,
    'toc_title': None,
    'use_fullscreen_button': True,
}

# Configure sidebar
html_sidebars = {
    "**": ["navbar-logo", "search-field", "sbt-sidebar-nav.html"]
}

# Source file suffixes
source_suffix = ['.rst', '.md']

# Configure numbering for auto-generated format docs but disable for main content
numfig = True
numfig_format = {
    'figure': 'Figure %s',
    'table': 'Table %s',
    'code-block': 'Listing %s',
    'section': 'Section %s'
}

# Disable automatic section numbering for cleaner look on main pages
html_use_smartypants = True

# Configure warnings - suppress auto-generated cross-reference warnings that can't be easily fixed
suppress_warnings = [
    'ref.ref',      # Suppress ref warnings for auto-generated content
    'ref.numref',   # Suppress numref warnings for auto-generated content
]

# Keep going on warnings and don't halt build
keep_warnings = False
nitpicky = False

# Configure cross-reference resolution
primary_domain = 'py'
default_role = 'py:obj'

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
    'hed': ('https://www.hedtags/hed-resources/', None),
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
    # Add custom CSS for modern styling
    try:
        app.add_css_file("theme_overrides.css")  # Used by newer Sphinx versions
    except AttributeError:
        app.add_stylesheet("theme_overrides.css")  # Used by older version of Sphinx

# -- Customize sphinx settings
autoclass_content = 'both'
autodoc_docstring_signature = True
autodoc_member_order = 'bysource'
add_function_parentheses = False

# Autodoc configuration for better API docs
autodoc_default_options = {
    'members': True,
    'inherited-members': True,
    'show-inheritance': True,
}


# -- HTML sphinx options
# (removed - using sphinx_book_theme configuration above)

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
