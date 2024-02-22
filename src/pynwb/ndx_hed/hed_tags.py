from collections.abc import Iterable
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from hed.errors import HedFileError, get_printable_issue_string
from hed.schema import HedSchema, HedSchemaGroup, load_schema_version, from_string
from hed.models import HedString
from pynwb import register_class
from pynwb.file import LabMetaData, NWBFile


@register_class('HedTags', 'ndx-hed')
class HedTags(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HedVersion.

    """

    __nwbfields__ = ('_hed_schema', 'hed_version')

    @docval({'name': 'name', 'type': 'str', 'doc': 'Must be HED', 'default': 'HED'},
            {'name': 'description', 'type': 'str', 'doc': 'Description of the HED annotations',
             'default': 'Hierarchical Event Descriptors (HED) annotations'},
            {'name': 'hed_version', 'type': 'str', 'doc': 'The version of HED used by this data.'},
            *get_docval(VectorData.__init__, 'data'))
    def __init__(self, **kwargs):
        hed_version = popargs('hed_version', kwargs)
        kwargs['name'] = 'HED'
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
            raise HedFileError("InvalidHEDData", "\n".join(issues), "")

    @docval({'name': 'val', 'type': str,
             'doc': 'the value to add to this column. Should be a valid HED string -- just forces string.'})
    def add_row(self, **kwargs):
        """Append a data value to this column."""
        val = getargs('val', kwargs)
        hed_obj = HedString(val, self._hed_schema)
        these_issues = hed_obj.validate()
        if these_issues:
            raise HedFileError("InvalidHEDValue",
                               f"{str(val)} issues: {get_printable_issue_string(these_issues)}", "")
        super().append(val)

    def get_hed_version(self):
        return self.hed_version

    def get_hed_schema(self):
        return self._hed_schema
    # # @docval({'name': 'schema', 'type': (HedSchema, None), 'doc': 'HedSchema to use to validate.', 'default': None},
    # #         {'name': 'return', 'type': 'list', 'doc': 'list of issues or none'})
    # def validate(self, schema, data):
    #     """Validate this VectorData. This is assuming a list --- where is the general iterator."""
    #     if not self._hed_schema:
    #         raise HedFileError('HedSchemaMissing', "Must provide a valid HedSchema", "")
    #     issues = []
    #     for index in range(len(data)):
    #         hed_obj = HedString(self.get(index), schema)
    #         these_issues = hed_obj.validate()
    #         if these_issues:
    #             issues.append(f"line {str(index)}: {get_printable_issue_string(these_issues)}")
    #     return "\n".join(issues)

    # def get_hed_schema(self):
    #     if not self._hed_schema:
    #         root = self._get_root()
    #         if isinstance(root, NWBFile):
    #             self._hed_schema = root.get_lab_meta_data("hed_version").get_schema()
    #     return self._hed_schema

    # def _get_root(self):
    #     root = self
    #     while hasattr(root, 'parent') and root.parent:
    #         root = root.parent
    #     if root == self:
    #         return None
    #    return root

        #     root = parent
        #     parent = root.parent
        # if parent:
        #     hed_version = parent.get_lab_meta_data("HedVersion")
        # else:
        #     hed_version = None
        # if hed_version:
        #     self.hed_schema = hed_version.get_schema()

    # root = self
    # parent = root.parent
    # while parent is not None:
    #     root = parent
    #     parent = root.parent
    # if parent:
    #     hed_version = parent.get_lab_meta_data("HedVersion")
    # else:
    #     hed_version = None
    # if hed_version:
    #     self.hed_schema = hed_version.get_schema()
