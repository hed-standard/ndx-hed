from collections.abc import Iterable
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from hed.schema import HedSchema, HedSchemaGroup, load_schema_version, from_string
from pynwb import register_class
from pynwb.file import LabMetaData, NWBFile
from ndx_hed import HedVersion


@register_class('HedTags', 'ndx-hed')
class HedTags(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HEDVersion.

    """

    __nwbfields__ = ('sub_name', '_hed_version')

    @docval(*get_docval(VectorData.__init__))
    def __init__(self, **kwargs):
        # kwargs['name'] = 'HED'
        super().__init__(**kwargs)
        self._hed_version = None
        self._init_internal()

    def _init_internal(self):
        """
        This finds the HED schema object of use in this NWBFile.

        TODO: How should errors be handled if this file doesn't have a HedVersion object in the LabMetaData?

        """
        self.sub_name = "HED"

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

    @docval({'name': 'return', 'type': 'list', 'doc': 'list of issues or none'})
    def validate(self):
        """Validate this VectorData. """
        hed_schema = self.get_hed_version()
        return True

    def get_hed_version(self): 
        if not self._hed_version:
            root = self._get_root()
            if isinstance(root, NWBFile):
                self._hed_version = root.get_lab_meta_data("HedVersion")
        return self._hed_version

    def _get_root(self):
        root = self
        while hasattr(root, 'parent') and root.parent:
            root = root.parent
        return root
 
 
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

