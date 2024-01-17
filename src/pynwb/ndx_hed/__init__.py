import os
from pynwb import load_namespaces, get_class

# Set path of the namespace.yaml file to the expected install location
ndx_hed_specpath = os.path.join(
    os.path.dirname(__file__),
    'spec',
    'ndx-events.namespace.yaml'
)

# If the extension has not been installed yet but we are running directly from
# the git repo
if not os.path.exists(ndx_hed_specpath):
    ndx_hed_specpath = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..',
        'spec',
        'ndx-hed.namespace.yaml'
    ))

# Load the namespace
load_namespaces(ndx_hed_specpath)
# 
# from . import io as __io  # noqa: E402,F401
# from .hed_models import NWBHedVersion
# 
# try:
#     from importlib.resources import files
# except ImportError:
#     # TODO: Remove when python 3.9 becomes the new minimum
#     from importlib_resources import files
# 
#     
# 
# # Get path to the namespace.yaml file with the expected location when installed not in editable mode
# __location_of_this_file = files(__name__)
# __spec_path = __location_of_this_file / "spec" / "ndx-hed.namespace.yaml"
# 
# # If that path does not exist, we are likely running in editable mode. Use the local path instead
# if not os.path.exists(__spec_path):
#     __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-hed.namespace.yaml"
# 
# # Load the namespace
# load_namespaces(str(__spec_path))
# 
# # TODO: Define your classes here to make them accessible at the package level.
# # Either have PyNWB generate a class from the spec using `get_class` as shown
# # below or write a custom class and register it using the class decorator
# # `@register_class("TetrodeSeries", "ndx-hed")`
# # HedAnnotations = get_class("HedAnnotations", "ndx-hed")
# HedVersion = get_class("HedVersion", "ndx-hed")
# 
# # Remove these functions from the package
del load_namespaces, get_class

from .hed_version import HedVersion
from .hed_tags import HedTags
from .hed_version1 import HedVersion1
