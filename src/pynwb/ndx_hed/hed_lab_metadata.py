"""The HED Lab Metadata class for storing HED (Hierarchical Event Descriptors) information."""

from hdmf.utils import docval, popargs
from hed.schema import load_schema_version
from pynwb import register_class
from pynwb.file import LabMetaData


@register_class("HedLabMetaData", "ndx-hed")
class HedLabMetaData(LabMetaData):
    """
    Stores the HED schema version for the NWBFile.

    """

    __nwbfields__ = ("_hed_schema", "hed_schema_version")

    @docval(
        {"name": "hed_schema_version", "type": "str", "doc": "The version of HED used by this data."},
        {
            "name": "name",
            "type": "str",
            "doc": "The name of the hed lab metadata (must be hed_schema).",
            "default": "hed_schema",
        },
    )
    def __init__(self, **kwargs):
        hed_schema_version = popargs("hed_schema_version", kwargs)
        if "name" in kwargs and kwargs["name"] != "hed_schema":
            raise ValueError(f"The 'name' for HedLabMetaData must be 'hed_schema', but '{kwargs['name']}' was given.")
        super().__init__(**kwargs)
        self.hed_schema_version = hed_schema_version
        self._init_internal()

    def _init_internal(self):
        """
        This loads (a private pointer to) the HED schema.
        """
        try:
            self._hed_schema = load_schema_version(self.hed_schema_version)
        except Exception as e:
            raise ValueError(f"Failed to load HED schema version {self.hed_schema_version}: {e}")

    def get_hed_schema_version(self):
        return self.hed_schema_version

    def get_hed_schema(self):
        return self._hed_schema
