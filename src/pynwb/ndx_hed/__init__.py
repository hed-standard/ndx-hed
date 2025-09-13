import os
from pynwb import load_namespaces, get_class

# Set path of the namespace.yaml file to the expected install location
ndx_hed_specpath = os.path.join(os.path.dirname(__file__), "spec", "ndx-hed.namespace.yaml")

# If the extension has not been installed yet, but we are running directly from the git repo
if not os.path.exists(ndx_hed_specpath):
    ndx_hed_specpath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "spec", "ndx-hed.namespace.yaml")
    )

# Load the namespace
load_namespaces(ndx_hed_specpath)

del load_namespaces, get_class

from .hed_tags import HedTags as HedTags
from .hed_tags import HedValueVector as HedValueVector
from .hed_lab_metadata import HedLabMetaData as HedLabMetaData
