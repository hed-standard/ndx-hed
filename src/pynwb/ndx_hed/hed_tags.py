from hdmf.common import VectorData
from hdmf.utils import docval, get_docval, getargs
from pynwb import register_class, register_map
from pynwb.event import DurationVectorData
from pynwb.io.core import VectorDataMap


@register_class("HedTags", "ndx-hed")
class HedTags(VectorData):
    """
    Column storing HED (Hierarchical Event Descriptors) annotations for a row. A HED string is a comma-separated,
    and possibly parenthesized list of HED tags selected from a valid HED vocabulary as specified by the
    NWBFile field HedVersion.

    A HedTags column must be named "HED" (enforced by the constructor). There is at most one HedTags
    column per DynamicTable (a consequence of the fixed name). HED-aware code also identifies HED
    columns by their neurodata type (``isinstance(col, HedTags)``).
    """

    #  __nwbfields__ = ('_hed_schema', 'hed_version')

    @docval(
        {
            "name": "name",
            "type": str,
            "doc": "The name of this column. Must be 'HED' (the default).",
            "default": "HED",
        },
        {
            "name": "description",
            "type": str,
            "doc": "a description for this column",
            "default": "Column that stores HED tags as text annotating their respective row.",
        },
        *get_docval(VectorData.__init__, "data"),
    )
    def __init__(self, **kwargs):
        if kwargs.get("name", "HED") != "HED":
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

    @docval({
        "name": "val",
        "type": str,
        "doc": "the value to add to this column. Should be a valid HED string -- just forces string.",
    })
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

    A HedValueVector column may have any name. HED-aware code identifies these columns by their
    neurodata type (``isinstance(col, HedValueVector)``), not by the column name.
    """

    __nwbfields__ = ("_hed",)

    @docval(
        *get_docval(VectorData.__init__, "name", "description", "data"),
        {"name": "hed", "type": str, "doc": "HED annotation template for all values in the column"},
    )
    def __init__(self, **kwargs):
        hed_annotation = kwargs.pop("hed", None)
        super().__init__(**kwargs)
        self._hed = _checked_template(self, hed_annotation)

    @property
    def hed(self):
        """Return the HED annotation template for this column."""
        return self._hed


@register_class("HedDurationVector", "ndx-hed")
class HedDurationVector(DurationVectorData):
    """
    The duration column of an EventsTable (durations in seconds) with a single HED annotation template that
    applies to all values in the column, as a HedValueVector does. It is a DurationVectorData, so code that
    reads event durations sees an ordinary duration column.

    HED-aware code treats it as a HedValueVector: the same rules apply (it may not appear in a MeaningsTable,
    and its values must satisfy the value class of the template's ``#`` tag). ``HED_TEMPLATE_TYPES`` holds both.
    """

    __nwbfields__ = ("_hed",)

    @docval(
        *get_docval(DurationVectorData.__init__, "name", "description", "data", "resolution"),
        {"name": "hed", "type": str, "doc": "HED annotation template for all values in the column"},
    )
    def __init__(self, **kwargs):
        hed_annotation = kwargs.pop("hed", None)
        super().__init__(**kwargs)
        self._hed = _checked_template(self, hed_annotation)

    @property
    def hed(self):
        """Return the HED annotation template for this column."""
        return self._hed


# The column types that carry one HED template with a single '#' for every value in the column.
HED_TEMPLATE_TYPES = (HedValueVector, HedDurationVector)


def _checked_template(column, hed_annotation: str) -> str:
    """Return the template of a HED template column, raising ValueError unless it has exactly one '#'."""
    placeholder_count = hed_annotation.count("#")
    if placeholder_count != 1:
        raise ValueError(
            f"{type(column).__name__} '{column.name}' template must contain exactly one '#' placeholder, "
            f"found {placeholder_count} in: {hed_annotation}"
        )
    return hed_annotation


class _HedColumnMap(VectorDataMap):
    """
    Object mapper of the HED column types that refuses to build a column in an NWBFile without a HedLabMetaData.

    The annotations cannot be validated without the HED schema version that the HedLabMetaData declares, so the
    file fails when it is written. Reading a file does not build, so existing files can still be read.
    """

    @docval(*get_docval(VectorDataMap.build))
    def build(self, **kwargs):
        column = getargs("container", kwargs)
        nwbfile = column.get_ancestor("NWBFile")
        if nwbfile is not None and "hed_schema" not in nwbfile.lab_meta_data:
            raise ValueError(
                f"{type(column).__name__} '{column.name}' of table '{column.parent.name}' holds HED annotations, "
                "but the NWBFile has no HedLabMetaData declaring the HED schema version. Add one with "
                "nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version=...)) before writing."
            )
        return super().build(**kwargs)


for _hed_column_type in (HedTags, *HED_TEMPLATE_TYPES):
    register_map(_hed_column_type, _HedColumnMap)
