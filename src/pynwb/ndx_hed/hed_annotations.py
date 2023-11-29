from collections.abc import Iterable
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from hed.schema import HedSchema, HedSchemaGroup, load_schema_version
from pynwb import register_class
from pynwb.file import LabMetaData


@register_class('HedAnnotations', 'ndx-hed')
class HedAnnotations(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HEDVersion.

    """

    __nwbfields__ = ('name', 'description', 'hed_strings')

    @docval({'name': 'name', 'type': str, 'doc': 'Must be HED'},
            {'name': 'description', 'type': str,
             'doc': 'Column name indicating that this column is of type HedAnnotations',
             'default': "Column name indicating that this column is of type HedAnnotations"},
            {'name': 'data', 'type': Iterable, 'shape': (None, ),  # required
             'doc': 'HED strings of type str.'}, *get_docval(VectorData.__init__, 'data'))
    def __init__(self, **kwargs):
        description, hed_strings = popargs('description', 'data', kwargs)
        kwargs['name'] = 'HED'
        super().__init__(**kwargs)
        self.description = description
        self.hed_strings = hed_strings
        self._init_internal()

    def _init_internal(self):
        """
        This finds the HED schema object of use in this NWBFile.

        TODO: How should errors be handled if this file doesn't have a HedVersion object in the LabMetaData?

        """
        root = self
        parent = root.parent
        while parent is not None:
            root = parent
            parent = root.parent
        hed_version = parent.get_lab_meta_data("HedVersion")
        if hed_version:
            self.hed_schema = hed_version.get_schema()

    @docval({'name': 'val', 'type': str,
             'doc': 'the value to add to this column. Should be a valid HED string.'})
    def add_row(self, **kwargs):
        """Append a data value to this column."""
        val = getargs('val', kwargs)
        # val.check_types()
        # TODO how to validate
        #
        # if val is not None and self.validate(val):
        #     if self.term_set.validate(term=val):
        #         self.append(val)
        #     else:
        #         msg = ("%s is not in the term set." % val)
        #         raise ValueError(msg)
        #
        # else:
        #     self.append(val)
        super().append(val)

    @docval({'name': 'key', 'type': 'str', 'doc': 'the value to add to this column'})
    def get(self, key):
        """
        Retrieve elements from this object.

        """
        # TODO: Can key be more than a single value?  Do we need to check validity of anything?
        vals = super().get(key)
        return vals

    @docval({'name': 'val', 'type': 'str', 'doc': 'the value to validate'},
            {'name': 'return', 'type': 'list', 'doc': 'list of issues or none'})
    def validate(self, **kwargs):
        """Validate this HED string"""
        val = getargs('val', kwargs)
        return True


@register_class("HedVersion", "ndx-hed")
class HedVersion(LabMetaData):
    """
    The class containing the HED versions and HED schema used in this data file.

    """

    __nwbfields__ = ('name', 'description', 'hed_version')

    @docval({'name': 'hed_version', 'type': (str, list),  'doc': 'HED strings of type str'})
    def __init__(self, hed_version):
        kwargs = {'name': 'hed_version'}
        super().__init__(**kwargs)
        self.hed_version = hed_version
        self._init_internal()

    def _init_internal(self):
        """
        Create a HedSchema or HedSchemaGroup object from the HED Versions
        """
        self._hed_schema = load_schema_version(self.hed_version)

    @docval(returns='The HED schema or schema group object for this version', rtype=(HedSchema, HedSchemaGroup))
    def get_hed_schema(self):
        return self._hed_schema
