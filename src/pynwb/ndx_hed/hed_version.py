from hdmf.utils import docval, getargs, get_docval, popargs
from pynwb import register_class
from pynwb.file import LabMetaData
from hed.schema import HedSchema, HedSchemaGroup, load_schema_version, from_string


@register_class("HedVersion", "ndx-hed")
class HedVersion(LabMetaData):
    """
    The class containing the HED versions and HED schema used in this data file.

    """

    __nwbfields__ = ('version', 'schema_string')

    # @docval({'name': 'version', 'type': str, 'doc': 'HED version of type str'},
    #         *get_docval(LabMetaData.__init__))
    @docval({'name': 'version', 'type': str,  'doc': 'HED strings of type str'})
    def __init__(self, **kwargs):
        version = popargs('version', kwargs)
        kwargs['name'] = 'hed_version'
        super().__init__(**kwargs)
        self.version = version
        self._init_internal()

    # @docval({'name': 'version', 'type': str, 'doc': 'HED version of type str'})
    # def __init__(self, version):
    #     kwargs = {'name': 'hed_version'}
    #     super().__init__(**kwargs)
    #     self.name = 'hed_version'
    #     self.version = version
    #     self._init_internal()

    def _init_internal(self):
        """
        Create a HED schema string
        """
        hed_schema = load_schema_version(self.version)
        self.schema_string = hed_schema.get_as_xml_string()

    @docval(returns='The HED schema version', rtype=str)
    def get_version(self):
        return self.version

    @docval(returns='The HED schema or schema group object for this version', rtype=(HedSchema, HedSchemaGroup))
    def get_schema(self):
        return from_string(self.schema_string)
