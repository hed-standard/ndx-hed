""" The HED Lab Metadata class for storing HED (Hierarchical Event Descriptors) information."""
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from hed.errors import get_printable_issue_string
from hed.schema import load_schema_version
from hed.models import HedString
from pynwb import register_class, LabMetaData


@register_class('HedLabMetaData', 'ndx-hed')
class HedLabMetaData(LabMetaData):
    """
    Stores the HED schema version for the NWBFile.

    """

    __nwbfields__ = ('_hed_schema', 'hed_version')

    @docval(*get_docval(LabMetatData.__init__),
            {'name': 'hed_version', 'type': 'str', 'doc': 'The version of HED used by this NWBFile.', 'default': '8.4.0'},)
    def __init__(self, **kwargs):
        hed_version = popargs('hed_version', kwargs)
        super().__init__(**kwargs)
        self.hed_version = hed_version
        self._init_internal()

    def _init_internal(self):
        """
        This loads (a private pointer to) the HED schema.
        """
        try:
            self._hed_schema = load_schema_version(self.hed_version)
        except Exception as e:
            raise ValueError(f"Failed to load HED schema version {self.hed_version}: {e}")

    def get_hed_version(self):
        return self.hed_version

    def get_hed_schema(self):
        return self._hed_schema
