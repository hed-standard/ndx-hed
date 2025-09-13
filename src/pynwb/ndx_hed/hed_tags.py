from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval
from pynwb import register_class


@register_class("HedTags", "ndx-hed")
class HedTags(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HedVersion.

    """

    #  __nwbfields__ = ('_hed_schema', 'hed_version')

    @docval(
        {"name": "name", "type": str, "doc": "The name of this VectorData", "default": "HED"},
        {
            "name": "description",
            "type": str,
            "doc": "a description for this column",
            "default": "Column that stores HED tags as text annotating their respective row.",
        },
        *get_docval(VectorData.__init__, "data"),
    )
    def __init__(self, **kwargs):
        if "name" in kwargs and kwargs["name"] != "HED":
            raise ValueError(f"The 'name' for HedTags must be 'HED', but '{kwargs['name']}' was given.")
        super().__init__(**kwargs)

    # def _init_internal(self):
    #     """
    #     This calls the tokenizer
    #     """
    #     self._hed_schema = load_schema_version(self.hed_version)
    #     issues = []
    #     if issues:
    #         issue_str = "\n".join(issues)
    #         raise ValueError(f"InvalidHEDData {issue_str}")

    @docval(
        {
            "name": "val",
            "type": str,
            "doc": "the value to add to this column. Should be a valid HED string -- just forces string.",
        }
    )
    def add_row(self, **kwargs):
        """Append a data value to this column."""
        val = getargs("val", kwargs)
        if not isinstance(val, str):
            raise TypeError(f"Value {val} is of incorrect type {type(val)}. Must be a string.")
        super().append(val)

    # def get_hed_version(self):
    #     return self.hed_version

    # def get_hed_schema(self):
    #     return self._hed_schema


@register_class("HedValueVector", "ndx-hed")
class HedValueVector(VectorData):
    """
    Column storing values and a single HED annotation that applies to all values in the column.
    A HED string is a comma-separated, and possibly parenthesized list of HED tags selected
    from a valid HED vocabulary as specified by the NWBFile field HedVersion.

    """

    __nwbfields__ = ("hed",)

    @docval(
        *get_docval(VectorData.__init__, "name", "description", "data"),
        {"name": "hed", "type": str, "doc": "HED tags for all values in the column"},
    )
    def __init__(self, **kwargs):
        hed_annotation = kwargs.pop("hed", None)
        super().__init__(**kwargs)
        self.hed = hed_annotation
