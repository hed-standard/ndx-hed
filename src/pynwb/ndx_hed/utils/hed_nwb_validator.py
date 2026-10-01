"""
HedNWBValidator: validation of the HED annotations in NWB DynamicTable objects.
"""

import io
import json
from typing import Any

import numpy as np
from hdmf.common import MeaningsTable
from hed.errors import ErrorContext, ErrorHandler, HedExceptions, HedFileError
from hed.errors.error_reporter import ROW_COUNT_KEY, check_for_any_errors
from hed.models import HedString, Sidecar, TabularInput
from hed.validator import HedValidator, SpreadsheetValidator
from hed.validator.util import placeholder_tag
from pynwb import NWBFile
from pynwb.core import DynamicTable
from pynwb.event import TimestampVectorData

from ..hed_lab_metadata import HedLabMetaData
from ..hed_tags import HedTags, HedValueVector
from .bids2nwb import _is_missing, get_bids_dataframe, get_json_hed_dict
from .hed_nwb_errors import HED_COLUMN_TYPE_INVALID, MEANINGS_VALUE_VECTOR_INVALID

# ROW_COUNT_KEY ("row_count") is hedtools' key for the number of rows holding a distinct value that an
# issue reports. It is imported above so that ``from ndx_hed.utils.hed_nwb_validator import ROW_COUNT_KEY``
# keeps working. Not an "ec_" key: hedtools treats every "ec_" key as an error context.
__all__ = ["HedNWBValidator", "ROW_COUNT_KEY"]

# The value class hedtools assumes for a placeholder whose tag declares none.
_TEXT_CLASS = "textClass"
_NUMERIC_CLASS = "numericClass"
_NAME_CLASS = "nameClass"


class HedNWBValidator:
    """
    Validates the HED annotations in NWB DynamicTable objects against the HED schema of a HedLabMetaData.

    ``validate_table`` is the table validator and ``validate_file`` calls it for every table in a file.
    ``validate_vector`` and ``validate_value_vector`` validate one column in isolation.
    """

    def __init__(self, hed_metadata: HedLabMetaData):
        """
        Initialize the HedNWBValidator with HED metadata.

        Parameters:
            hed_metadata (HedLabMetaData): The HED lab metadata holding the schema and the definitions. A
                constructed HedLabMetaData has already loaded and checked both, so nothing is validated here.

        Raises:
            ValueError: If hed_metadata is not an instance of HedLabMetaData
        """
        if not isinstance(hed_metadata, HedLabMetaData):
            raise ValueError("hed_metadata must be an instance of HedLabMetaData")

        self.hed_metadata = hed_metadata
        self.hed_schema = hed_metadata.get_hed_schema()
        self.def_dict = hed_metadata.get_definition_dict()
        # For the single-column helpers: the template check of validate_value_vector, and hedtools' stage
        # methods, which take the definitions from the constructor when called on their own. validate_table
        # builds its own SpreadsheetValidator per call, since validate() replaces the definitions with the
        # sidecar's for the run.
        self._hed_validator = HedValidator(self.hed_schema, def_dicts=self.def_dict)
        self._column_validator = SpreadsheetValidator(self.hed_schema, def_dicts=self.def_dict)

    # ------------------------------------------------------------------------------------------
    # The table validator

    def validate_table(
        self, table: DynamicTable, error_handler: ErrorHandler | None = None, assemble: bool = True
    ) -> list[dict[str, Any]]:
        """
        Validates the HED annotations of a DynamicTable.

        The steps, in order. "Stops" means the issues found so far for this table are returned and
        the later steps do not run for it.

        1. Structural rules (``docs/source/hed_validation.md``): a column named ``HED``, in the table or
           in any of its MeaningsTables, must be a HedTags (``HED_COLUMN_TYPE_INVALID``); a MeaningsTable
           must not contain a HedValueVector (``MEANINGS_VALUE_VECTOR_INVALID``). An issue stops.
        2. A table with no HedTags column, no HedValueVector column, and no MeaningsTable with a ``HED``
           column has nothing to validate and returns ``[]`` without being read.
        3. The table's column metadata is converted to a BIDS sidecar dict with ``get_json_hed_dict``,
           which reads no table data. The definitions of the HedLabMetaData travel in the sidecar, as
           BIDS carries them.
        4. hedtools' staged tabular validation (``SpreadsheetValidator.validate``) runs on the table
           through a column source that reads one column at a time, each stage stopping on an error:
           the sidecar (HedValueVector templates, MeaningsTable HED, definitions, ``{column}``
           references); the column values, that is each HedValueVector's distinct values against the
           units and value class of its template's ``#`` tag (rule R7, with the value in place, then the
           basic syntax checks on the substituted tag) and each categorical column's distinct values
           against its levels (``SIDECAR_KEY_MISSING``, a warning); the ``HED`` column, each distinct
           string once with the basic checks; then the assembly gate. With ``assemble=True`` (the
           default) the whole table is read into a BIDS dataframe with ``get_bids_dataframe`` and each
           row's HED is assembled from its ``HED`` cell, its categorical HED, and its value templates
           and validated as a whole, with the temporal checks over the rows when the table has a
           ``TimestampVectorData`` column (exported as ``onset``). With ``assemble=False`` the table is
           never converted to a dataframe: the group-level checks run on each distinct ``HED`` string
           instead, and nothing that needs the other tags of a row or the other rows is checked.

        A HedValueVector whose dtype settles the value class is not read at all: a numeric column passes
        textClass, an integer column passes numericClass and nameClass, and a float column under
        numericClass is scanned once for infinities, which are not numeric values.

        Every issue carries the table name in ``ec_table_name``. A sidecar issue carries the column in
        ``ec_sidecarColumnName`` and, for categorical HED, the value in ``ec_sidecarKeyName``, and has no
        row. A row issue carries ``ec_column`` and ``ec_row``, the table row index (the first data row is
        0) in both modes. The values of a HedValueVector and the strings of the ``HED`` column are
        validated by distinct value in both modes: each is validated once, reported at the first row
        holding it, with the number of rows that hold it in ``row_count``.

        Parameters:
            table (DynamicTable): The table to validate. Not a MeaningsTable: its HED is validated as
                part of the table whose column it annotates.
            error_handler (ErrorHandler, optional): Collects the issues. A new one that drops warnings
                is created if None.
            assemble (bool): Whether to run the assembled (row and temporal) validation. Default True.

        Returns:
            list[dict[str, Any]]: The validation issues for the table.

        Raises:
            ValueError: If table is not a DynamicTable, or is a MeaningsTable.
        """
        if table is None or not isinstance(table, DynamicTable):
            raise ValueError("The provided table is not a valid DynamicTable instance.")
        if isinstance(table, MeaningsTable):
            raise ValueError(
                f"MeaningsTable '{table.name}' cannot be validated on its own: its HED is validated as part of "
                "the table whose column it annotates. Pass that table instead."
            )
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)

        # The context is popped in a finally block so that an exception raised while validating does not
        # leave a stale context on a caller-provided error handler.
        error_handler.push_error_context(ErrorContext.TABLE_NAME, table.name)
        try:
            return self._validate_table_in_context(table, error_handler, assemble)
        finally:
            error_handler.pop_error_context()

    def _validate_table_in_context(
        self, table: DynamicTable, error_handler: ErrorHandler, assemble: bool
    ) -> list[dict[str, Any]]:
        """Body of validate_table, run with the TABLE_NAME context already pushed."""
        issues = self._check_structure(table, error_handler)
        if issues:
            return issues
        if not self._has_hed(table):
            return []

        # The sidecar half of the BIDS conversion reads only the column metadata and the MeaningsTables;
        # the table's data is read column by column where a hedtools stage needs it.
        json_data = get_json_hed_dict(table, self.hed_metadata)
        sidecar = Sidecar(io.StringIO(json.dumps(json_data)), name=table.name) if json_data else None
        source = _DynamicTableSource(table, self.hed_schema, self.def_dict, assemble, sidecar)

        # The definitions travel in the sidecar; a table whose sidecar dict is empty (a bare HED column
        # and no definitions) gets them directly. name="" keeps hedtools from pushing its own FILE_NAME
        # context: the table's location is the TABLE_NAME context already pushed, plus the FILE_NAME that
        # validate_file pushes. row_offset=0 reports table row indices rather than BIDS file lines.
        return SpreadsheetValidator(self.hed_schema).validate(
            source,
            sidecar=sidecar,
            extra_def_dicts=None if sidecar is not None else self.def_dict,
            name="",
            error_handler=error_handler,
            row_offset=0,
        )

    # ------------------------------------------------------------------------------------------
    # Step 1: structural rules

    @staticmethod
    def _check_structure(table: DynamicTable, error_handler: ErrorHandler) -> list[dict[str, Any]]:
        """Return the structural issues of a table and its MeaningsTables (rules R5 and R6)."""
        issues = []
        for owner in [table, *table.meanings_tables.values()]:
            for column in owner.columns:
                if column.name == "HED" and not isinstance(column, HedTags):
                    issues += error_handler.format_error_with_context(
                        HED_COLUMN_TYPE_INVALID, table_name=owner.name, column_type=type(column).__name__
                    )
                if isinstance(owner, MeaningsTable) and isinstance(column, HedValueVector):
                    issues += error_handler.format_error_with_context(
                        MEANINGS_VALUE_VECTOR_INVALID, table_name=owner.name, column_name=column.name
                    )
        return issues

    @staticmethod
    def _has_hed(table: DynamicTable) -> bool:
        """Return True if the table carries any HED: a HedTags or HedValueVector column, or categorical HED."""
        if any(isinstance(column, (HedTags, HedValueVector)) for column in table.columns):
            return True
        return any("HED" in meanings.colnames for meanings in table.meanings_tables.values())

    # ------------------------------------------------------------------------------------------
    # The file validator

    def validate_file(
        self, nwbfile: NWBFile, error_handler: ErrorHandler | None = None, assemble: bool = True
    ) -> list[dict[str, Any]]:
        """
        Validates the HED annotations of every DynamicTable in an NWB file.

        The file must hold a HedLabMetaData named ``hed_schema`` whose schema version matches the
        validator's. Every DynamicTable except a MeaningsTable is then passed to ``validate_table``; a
        MeaningsTable is covered by the table whose column it annotates. Every issue carries the file
        identifier in ``ec_filename`` and its table in ``ec_table_name``.

        Parameters:
            nwbfile (NWBFile): The NWB file to validate
            error_handler (ErrorHandler, optional): Collects the issues. A new one that drops warnings
                is created if None.
            assemble (bool): Passed to ``validate_table``. Default True.

        Returns:
            list[dict[str, Any]]: The validation issues of all tables in the file

        Raises:
            ValueError: If nwbfile is not a valid NWBFile instance
            HedFileError: If HedLabMetaData is missing or invalid in the NWB file
            HedFileError: If the HED schema version in the NWB file does not match the validator's schema version
        """
        if nwbfile is None or not isinstance(nwbfile, NWBFile):
            raise ValueError("The provided nwbfile is not a valid NWBFile instance.")

        hed_metadata = nwbfile.lab_meta_data.get("hed_schema")
        if hed_metadata is None or not isinstance(hed_metadata, HedLabMetaData):
            raise HedFileError(
                HedExceptions.SCHEMA_INVALID, f"NWB file {nwbfile.identifier} does not have a valid HED schema", ""
            )

        if hed_metadata.get_hed_schema_version() != self.hed_schema.version:
            raise HedFileError(
                HedExceptions.SCHEMA_VERSION_INVALID,
                f"HED schema version in NWB file ({hed_metadata.get_hed_schema_version()})"
                + " does not match validator schema version"
                + f"({self.hed_schema.version})",
                "",
            )

        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)

        issues = []
        error_handler.push_error_context(ErrorContext.FILE_NAME, nwbfile.identifier)
        try:
            for obj in nwbfile.all_children():
                if not isinstance(obj, DynamicTable) or isinstance(obj, MeaningsTable):
                    continue
                issues += self.validate_table(obj, error_handler, assemble=assemble)
        finally:
            error_handler.pop_error_context()
        return issues

    # ------------------------------------------------------------------------------------------
    # Single-column helpers

    def validate_vector(self, hed_tags: HedTags, error_handler: ErrorHandler | None = None) -> list[dict[str, Any]]:
        """
        Validates the annotations of a HedTags column in isolation, each distinct string once.

        Each distinct HED string of the column is checked on its own: the basic checks and the
        group-level checks (hedtools ``validate_hed_column`` with ``full_string=True``). The required-tag
        check needs the assembled row and does not run. The helper does not see the other columns of the
        row, the categorical HED of a MeaningsTable, or the other rows, so use ``validate_table`` for a
        table. An issue is reported at the first row holding the string, with the number of rows that
        hold it in ``row_count``.

        Parameters:
            hed_tags (HedTags): The HedTags column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            list[dict[str, Any]]: A list of validation issues found in the HedTags column
        """
        if hed_tags is None or not isinstance(hed_tags, HedTags):
            raise ValueError("The provided hed_tags is not a valid HedTags instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        # Slice once: on a file-backed column, iterating the dataset directly is one HDF5 read per row.
        distinct = _distinct_values(hed_tags.data[:])
        return self._column_validator.validate_hed_column(
            hed_tags.name, distinct, error_handler, row_offset=0, full_string=True
        )

    def validate_value_vector(
        self, hed_values: HedValueVector, error_handler: ErrorHandler | None = None
    ) -> list[dict[str, Any]]:
        """
        Validates a HedValueVector column in isolation: the template on its own, then the values.

        The template is validated with placeholders allowed and with any ``{column}`` references
        removed first: a reference is resolved against the table's other columns by ``validate_table``
        (hedtools' sidecar validation), which this single-column helper cannot do. If the template has
        an error the values are not checked. Otherwise each distinct non-missing value is checked as the
        ``#`` tag alone with the value in place, for its units and value class and then the basic syntax
        checks on the substituted tag, exactly as ``validate_table`` does (rule R7, hedtools
        ``validate_value_column``); an issue is reported at the first row holding the value with the
        number of rows in ``row_count``. A column whose dtype settles the value class is not read.

        Parameters:
            hed_values (HedValueVector): The HedValueVector column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            list[dict[str, Any]]: A list of validation issues found in the HedValueVector column
        """
        if hed_values is None or not isinstance(hed_values, HedValueVector) or hed_values.hed is None:
            raise ValueError("The provided hed_values is not a valid HedValueVector instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)

        # The template on its own, with the references removed from the parsed string and the object
        # validated, as hedtools' sidecar validator does. The text is not parsed again: a template whose
        # parentheses do not balance parses to an empty tree whose text is "", and the structural checks
        # report on the raw string the object still carries. Under the column context, like the value
        # check that follows, so every issue of the helper names the column.
        hed_template = HedString(hed_values.hed, self.hed_schema, def_dict=self.def_dict)
        hed_template.remove_refs()
        error_handler.push_error_context(ErrorContext.COLUMN, hed_values.name)
        try:
            issues = self._hed_validator.validate(hed_template, allow_placeholders=True, error_handler=error_handler)
        finally:
            error_handler.pop_error_context()
        if check_for_any_errors(issues):
            return issues

        distinct = _value_column_distinct(hed_values, self.hed_schema, self.def_dict)
        return issues + self._column_validator.validate_value_column(
            hed_values.name, hed_values.hed, distinct, error_handler, row_offset=0
        )


# ----------------------------------------------------------------------------------------------
# The column source hedtools reads the table through


class _DynamicTableSource:
    """
    A hedtools ``ColumnSource`` over a DynamicTable: the table as hedtools' staged validator reads it.

    The validator asks for the column names, then for the distinct values of one column at a time (the
    value columns, the categorical columns, the ``HED`` column), and only at the assembly stage for a
    ``TabularInput``. So a column is read only when a stage needs it, a HedValueVector whose dtype
    settles its value class is not read at all, and without assembly no dataframe is ever built.
    Columns are named as BIDS names them: a ``TimestampVectorData`` named ``timestamp`` is ``onset``,
    the rename ``get_bids_dataframe`` makes.
    """

    def __init__(self, table: DynamicTable, hed_schema, def_dict, assemble: bool, sidecar: Sidecar | None):
        self._table = table
        self._hed_schema = hed_schema
        self._def_dict = def_dict
        self._assemble = assemble
        self._sidecar = sidecar
        self._distinct: dict[str, dict[str, list[int]]] = {}  # BIDS column name -> distinct values, once read
        self._table_names: dict[str, str] = {}  # BIDS column name -> table column name
        for name in table.colnames:
            bids_name = "onset" if name == "timestamp" and isinstance(table[name], TimestampVectorData) else name
            self._table_names[bids_name] = name

    def column_names(self) -> list[str]:
        return list(self._table_names)

    def distinct_values(self, column_name: str) -> dict[str, list[int]]:
        table_name = self._table_names.get(column_name)
        if table_name is None:
            return {}
        # Each column is read once per validation: without assembly hedtools asks for the HED column
        # twice, for the basic checks and then for the group-level checks on the same strings.
        if column_name not in self._distinct:
            column = self._table[table_name]
            if isinstance(column, HedValueVector):
                self._distinct[column_name] = _value_column_distinct(column, self._hed_schema, self._def_dict)
            else:
                # Slice once: on a file-backed column, iterating the dataset directly is one HDF5 read per row.
                self._distinct[column_name] = _distinct_values(column.data[:])
        return self._distinct[column_name]

    def column_mapper(self):
        return None  # hedtools builds the TabularInput-style mapper from the sidecar

    def as_base_input(self) -> TabularInput | None:
        if not self._assemble:
            return None
        # Assembly needs every column of the table as a BIDS dataframe; built here so that it exists
        # only for the assembly stage, after the column stages have passed.
        return TabularInput(file=get_bids_dataframe(self._table), sidecar=self._sidecar, name=self._table.name)


# ----------------------------------------------------------------------------------------------
# Module helpers


def _value_column_distinct(column: HedValueVector, hed_schema, def_dict) -> dict[str, list[int]]:
    """
    Return the distinct values of a HedValueVector that need checking against its template's ``#`` tag.

    The column is not read when its dtype settles the question: a numeric column satisfies textClass and
    an integer column numericClass and nameClass (``_dtype_settles``). A float column under numericClass
    is scanned once for infinities, which are not numeric values ("Age/inf s" fails), and only those are
    returned. A template without a checkable placeholder has nothing to check. Otherwise the column is
    read once.
    """
    placeholder = placeholder_tag(column.hed, hed_schema, def_dict)
    if placeholder is None:
        return {}
    classes = set(placeholder.value_classes) or {_TEXT_CLASS}
    dtype = _column_dtype(column)
    if _dtype_settles(dtype, classes):
        return {}
    if dtype is not None and dtype.kind == "f" and _NUMERIC_CLASS in classes:
        values = np.asarray(column.data[:], dtype=float)
        infinite = np.isinf(values)
        if not infinite.any():
            return {}
        return _distinct_values(np.where(infinite, values, np.nan))
    return _distinct_values(column.data[:])


def _column_dtype(column) -> np.dtype | None:
    """Return the dtype of a column's data without reading it, or None if it has none (a Python list)."""
    dtype = getattr(column.data, "dtype", None)
    if dtype is not None:
        return np.dtype(dtype)
    if isinstance(column.data, list) and column.data:
        return np.asarray(column.data).dtype
    return None


def _dtype_settles(dtype: np.dtype | None, value_classes: set[str]) -> bool:
    """
    Return True if the dtype alone proves every value satisfies one of the value classes.

    A number's text has only digits, a sign, a period, and an exponent letter, so it satisfies
    textClass, and an integer's text satisfies numericClass and nameClass (a bare integer is a valid
    name and a negative one adds only a hyphen). A float satisfies numericClass only when finite
    ("inf" is not a numeric value), so a float column under numericClass is not settled here; the
    caller scans it for infinities. Nothing about a string or object dtype is settled.
    """
    if dtype is None:
        return False
    if dtype.kind in "iuf" and _TEXT_CLASS in value_classes:
        return True
    return dtype.kind in "iu" and (_NUMERIC_CLASS in value_classes or _NAME_CLASS in value_classes)


def _distinct_values(values) -> dict[str, list[int]]:
    """
    Map each distinct non-missing value, as text, to the rows holding it. Missing is None, NaN, "", "n/a".

    The same mapping as hedtools' ``distinct_values``, with ndx-hed's ``_is_missing`` for the NaN test:
    an NWB column may hold numpy float32 or float16 NaNs, which are not instances of Python's float.
    """
    distinct: dict[str, list[int]] = {}
    for row, value in enumerate(values):
        if _is_missing(value):
            continue
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        text = str(value)
        if text == "n/a":
            continue
        distinct.setdefault(text, []).append(row)
    return distinct
