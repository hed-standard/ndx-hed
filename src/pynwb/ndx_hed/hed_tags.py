
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from hed.errors import get_printable_issue_string
from hed.schema import load_schema_version
from hed.models import HedString
from pynwb import register_class


@register_class('HedTags', 'ndx-hed')
class HedTags(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HedVersion.

    """

    __nwbfields__ = ('_hed_schema', 'hed_version')

    @docval({'name': 'hed_version', 'type': 'str', 'doc': 'The version of HED used by this data.'},
            {'name': 'name', 'type': str, 'doc': 'The name of this VectorData', 'default': 'HED'},
            {'name': 'description', 'type': str, 'doc': 'a description for this column',
             'default': "Column that stores HED tags as text annotating their respective row."},
            *get_docval(VectorData.__init__, 'data'))
    def __init__(self, **kwargs):
        hed_version = popargs('hed_version', kwargs)
        super().__init__(**kwargs)
        self.hed_version = hed_version
        self._init_internal()

    def _init_internal(self):
        """
        This loads (a private pointer to) the HED schema and validates the HED data.
        """
        self._hed_schema = load_schema_version(self.hed_version)
        issues = []
        for index in range(len(self.data)):
            hed_obj = HedString(self.get(index), self._hed_schema)
            these_issues = hed_obj.validate()
            if these_issues:
                issues.append(f"line {str(index)}: {get_printable_issue_string(these_issues)}")
        if issues:
            issue_str = "\n".join(issues)
            raise ValueError(f"InvalidHEDData {issue_str}")

    @docval({'name': 'val', 'type': str,
             'doc': 'the value to add to this column. Should be a valid HED string -- just forces string.'})
    def add_row(self, **kwargs):
        """Append a data value to this column."""
        val = getargs('val', kwargs)
        hed_obj = HedString(val, self._hed_schema)
        these_issues = hed_obj.validate()
        if these_issues:
            raise ValueError(f"InvalidHEDValue [{str(val)}] issues: {get_printable_issue_string(these_issues)}")
        super().append(val)

    def get_hed_version(self):
        return self.hed_version

    def get_hed_schema(self):
        return self._hed_schema
