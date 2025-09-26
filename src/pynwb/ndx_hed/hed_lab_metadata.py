"""The HED Lab Metadata class for storing HED (Hierarchical Event Descriptors) information."""

from typing import Union
from hdmf.utils import docval, popargs
from hed.errors import get_printable_issue_string, ErrorSeverity
from hed.schema import load_schema_version, HedSchema, HedSchemaGroup
from hed.models import DefinitionDict
from pynwb import register_class
from pynwb.file import LabMetaData


@register_class("HedLabMetaData", "ndx-hed")
class HedLabMetaData(LabMetaData):
    """
    Stores the HED schema version for the NWBFile.

    """

    __nwbfields__ = ("_hed_schema", "hed_schema_version", "_definition_dict")

    @docval(
        {"name": "hed_schema_version", "type": "str", "doc": "The version of HED used by this data."},
        {
            "name": "definitions",
            "type": "str",
            "doc": "A string containing one or more HED definitions.",
            "default": None,
        },
        {
            "name": "name",
            "type": "str",
            "doc": "The name of the hed lab metadata (must be hed_schema).",
            "default": "hed_schema",
        },
    )
    def __init__(self, **kwargs):
        hed_schema_version = popargs("hed_schema_version", kwargs)
        definitions = popargs("definitions", kwargs)
        if "name" in kwargs and kwargs["name"] != "hed_schema":
            raise ValueError(f"The 'name' for HedLabMetaData must be 'hed_schema', but '{kwargs['name']}' was given.")
        super().__init__(**kwargs)
        self.hed_schema_version = hed_schema_version
        self._init_internal(definitions)

    @property
    def definitions(self):
        """Get the definitions as a string."""
        if len(self._definition_dict.defs) == 0:
            return None
        return self.extract_definitions()

    def _init_internal(self, original_definitions: Union[str, list, dict, None]):
        """
        Load the HED schema and initialize the internal DefinitionDict.

        This internal method is called during initialization to set up the
        HED schema object and create a DefinitionDict from any provided definitions.

        Parameters:
            original_definitions (str or list or Dict[str, DefinitionEntry] or None): 
                A string containing one or more HED definitions,
                a list of such strings, a dict of DefinitionEntry objects, or None.
                If None or empty, an empty DefinitionDict is created.
                
        Raises:
            ValueError: If the HED schema version cannot be loaded or if the
                       definitions cannot be parsed into a valid DefinitionDict.
        """
        try:
            self._hed_schema = load_schema_version(self.hed_schema_version)
        except Exception as e:
            raise ValueError(f"Failed to load HED schema version {self.hed_schema_version}: {e}")

        try:
            self._definition_dict = DefinitionDict(original_definitions, self._hed_schema)
            errors = [issue for issue in self._definition_dict.issues if issue["severity"] < ErrorSeverity.WARNING]
            if errors:
                raise ValueError(
                    f"DefinitionDict has issues: {get_printable_issue_string(self._definition_dict.issues)}"
                )
        except Exception as e:
            raise ValueError(f"Failed to create DefinitionDict for HedLabMetaData: {e}")

    def add_definitions(self, defs: Union[str, list, dict, None]):
        """
        Add new definitions to the existing definition dictionary.

        Args:
            defs (str or list or dict or None): A string containing one or more HED definitions,
                                                a list of such strings, a dict of DefinitionEntry objects, or None.
                       If None or empty, no action is taken.
        """
        if not defs:
            return
        self._definition_dict.add_definitions(defs, self._hed_schema)

    def get_definition_dict(self) -> DefinitionDict:
        """
        Get the internal DefinitionDict object.

        Returns:
            DefinitionDict: The internal DefinitionDict containing all definitions.
        """
        return self._definition_dict

    def get_hed_schema_version(self):
        """
        Get the HED schema version string.

        Returns:
            str: The HED schema version used by this metadata object.
        """
        return self.hed_schema_version

    def get_hed_schema(self) -> Union[HedSchema, HedSchemaGroup]:
        """
        Get the loaded HED schema object.

        Returns:
            HedSchema or HedSchemaGroup: The loaded HED schema object.
        """
        return self._hed_schema

    def extract_definitions(self) -> str:
        """
        Extract definitions as string (for serialization).

        Returns:
            str: A string representation of the definitions.
        """
        def_list = []
        for def_name, def_entry in self._definition_dict.items():
            takes_value = "/#" if def_entry.takes_value else ""
            def_str = f"(Definition/{def_name}{takes_value},{def_entry.contents})"
            def_list.append(def_str)
        return ",".join(def_list)
