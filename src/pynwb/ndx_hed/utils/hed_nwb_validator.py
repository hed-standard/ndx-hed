"""
HedNWBValidator: validation of the HED annotations in NWB DynamicTable objects.
"""

import io
import json
import math
from typing import Any

import numpy as np
from hdmf.common import MeaningsTable
from hed.errors import ErrorContext, ErrorHandler, HedExceptions, HedFileError
from hed.errors.error_reporter import check_for_any_errors
from hed.errors.error_types import ValidationErrors
from hed.models import HedString, Sidecar, TabularInput
from pynwb import NWBFile
from pynwb.core import DynamicTable

from ..hed_lab_metadata import HedLabMetaData
from ..hed_tags import HedTags, HedValueVector
from .bids2nwb import _is_missing, get_bids_dataframe, get_json_hed_dict
from .hed_nwb_errors import HED_COLUMN_TYPE_INVALID, MEANINGS_VALUE_VECTOR_INVALID

# hedtools reports the line of the BIDS TSV file, where the header is line 1, so data row i is
# reported as i + 2 (hed/validator/spreadsheet_validator.py, row_adj). ndx-hed reports the table
# row index instead, so the assembled path subtracts this.
_BIDS_ROW_OFFSET = 2

# The value class hedtools assumes for a placeholder whose tag declares none.
_TEXT_CLASS = "textClass"
_NUMERIC_CLASS = "numericClass"
_NAME_CLASS = "nameClass"

# Extra key on an issue from a distinct-value pass: how many rows hold the annotation reported. Not an
# "ec_" key: hedtools treats every "ec_" key as an error context and get_printable_issue_string would
# fail on one it does not know.
ROW_COUNT_KEY = "row_count"


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
        4. The sidecar (HedValueVector templates, MeaningsTable HED, definitions) is validated with
           hedtools ``Sidecar.validate``. Any error stops: such an error would repeat on every row that
           uses it, and the row annotations assembled from it cannot be trusted. Warnings do not stop.
        5. The values of every HedValueVector column are checked against the value class of the
           template's ``#`` tag. A numeric column passes without being read when the class is text,
           and an integer column when it is numeric or a name; a float column under a numeric class is
           scanned once for infinities, which are not numeric values; otherwise the column is read once
           and each distinct value is substituted into the template and validated once. Any error stops.
        6. The assembly gate. With ``assemble=True`` (the default) the whole table is read into a BIDS
           dataframe with ``get_bids_dataframe`` and hedtools ``TabularInput.validate`` runs: each cell
           on its own, the categorical values against their levels, each row's HED assembled from its
           ``HED`` cell, its categorical HED, and its value templates, and, when the table has a
           ``TimestampVectorData`` column (exported as ``onset``), the temporal checks over the rows.
           With ``assemble=False`` the table is never converted to a dataframe: ndx-hed reads the ``HED``
           column and validates it cell by cell, reads each categorical column to check its values
           against their levels, and runs nothing that needs the other tags of a row or the other rows.

        Every issue carries the table name in ``ec_table_name``. A sidecar issue carries the column in
        ``ec_sidecarColumnName`` and, for categorical HED, the value in ``ec_sidecarKeyName``, and has no
        row. A row issue carries ``ec_column`` and ``ec_row``, the table row index (the first data row is
        0) in both modes. Where ndx-hed validates distinct values itself (the HedValueVector values in
        step 5, and the ``HED`` column with ``assemble=False``), each distinct annotation is validated
        once, reported at the first row holding it, with the number of rows that hold it in
        ``row_count``.

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
        # the table's data is read only where a step below needs it.
        json_data = get_json_hed_dict(table, self.hed_metadata)

        # Steps 4 and 5 stop the table on any error. Their warnings are kept only where nothing later
        # would report them: in the no-assembly path, and when a step stops the table. In the assembled
        # path TabularInput re-reports a sidecar or value warning on every row that uses the annotation,
        # so adding them here as well would report each twice; only the warnings for categorical levels
        # that no row uses are added back after assembly.
        sidecar = None
        sidecar_issues = []
        if json_data:
            # name="" keeps hedtools from pushing its own FILE_NAME context: the table's location is the
            # TABLE_NAME context already pushed, plus the FILE_NAME that validate_file pushes.
            sidecar = Sidecar(io.StringIO(json.dumps(json_data)), name=table.name)
            sidecar_issues = sidecar.validate(self.hed_schema, name="", error_handler=error_handler)
            if check_for_any_errors(sidecar_issues):
                return sidecar_issues

        value_issues = self._check_value_vectors(table, error_handler)
        if check_for_any_errors(value_issues):
            return sidecar_issues + value_issues

        if not assemble:
            issues += sidecar_issues + value_issues
            issues += self._validate_hed_column(table, error_handler)
            issues += self._check_categorical_coverage(table, error_handler)
            return issues

        # Assembly needs every column of the table as a BIDS dataframe.
        df = get_bids_dataframe(table)
        tab_input = TabularInput(file=df, sidecar=sidecar, name=table.name)
        tab_issues = tab_input.validate(self.hed_schema, name="", error_handler=error_handler)
        _shift_rows(tab_issues, -_BIDS_ROW_OFFSET)
        issues += tab_issues
        # TabularInput only sees categorical values that occur in the data, so add the sidecar warnings
        # for categorical levels that never appear (otherwise they would be missed).
        issues += self._unused_categorical_level_issues(sidecar_issues, df, json_data)
        return issues

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
    # Step 5: HedValueVector values against the value class of the placeholder

    def _check_value_vectors(self, table: DynamicTable, error_handler: ErrorHandler) -> list[dict[str, Any]]:
        issues = []
        for column in table.columns:
            if not isinstance(column, HedValueVector):
                continue
            error_handler.push_error_context(ErrorContext.COLUMN, column.name)
            try:
                issues += self._check_value_vector(column, error_handler)
            finally:
                error_handler.pop_error_context()
        return issues

    def _check_value_vector(self, column: HedValueVector, error_handler: ErrorHandler) -> list[dict[str, Any]]:
        """Check the values of one HedValueVector; see validate_table step 5."""
        dtype = _column_dtype(column)
        classes = self._placeholder_value_classes(column.hed)
        if _dtype_settles(dtype, classes):
            return []
        if dtype is not None and dtype.kind == "f" and _NUMERIC_CLASS in classes:
            # A finite float is a numeric value, but inf is not ("Age/inf s" fails numericClass). One
            # vectorized pass over the column finds the infinities; only those are substituted.
            values = np.asarray(column.data[:], dtype=float)
            infinite = np.isinf(values)
            if not infinite.any():
                return []
            distinct = _distinct_values(np.where(infinite, values, np.nan))
        else:
            distinct = _distinct_values(column.data[:])
        issues = []
        for value, rows in distinct.items():
            issues += self._validate_once(column.hed.replace("#", value), rows, error_handler)
        return issues

    def _placeholder_value_classes(self, template: str) -> set[str]:
        """
        Return the value classes of the ``#`` tag of a template, or {textClass} if it declares none.

        For a ``Def/Name/#`` template the ``#`` fills the placeholder inside the definition, so the
        classes are those of the placeholder tag in the definition's body.
        """
        hed_string = HedString(template, self.hed_schema, def_dict=self.def_dict)
        for tag in hed_string.get_all_tags():
            if "#" not in tag.extension:
                continue
            if tag.short_base_tag.lower() == "def":
                entry = self.def_dict.get(tag.extension.split("/")[0])
                if entry is None or not entry.takes_value:
                    break
                tag = next((inner for inner in entry.contents.get_all_tags() if "#" in inner.extension), None)
                if tag is None:
                    break
            classes = set(tag.value_classes)
            return classes if classes else {_TEXT_CLASS}
        return {_TEXT_CLASS}

    # ------------------------------------------------------------------------------------------
    # Step 6 without assembly: the HED column cell by cell, categorical values against their levels

    def _validate_hed_column(self, table: DynamicTable, error_handler: ErrorHandler) -> list[dict[str, Any]]:
        """Validate each distinct annotation of the table's HedTags column once."""
        issues = []
        for column in table.columns:
            if not isinstance(column, HedTags):
                continue
            error_handler.push_error_context(ErrorContext.COLUMN, column.name)
            try:
                for annotation, rows in _distinct_values(column.data[:]).items():
                    issues += self._validate_once(annotation, rows, error_handler)
            finally:
                error_handler.pop_error_context()
        return issues

    @staticmethod
    def _check_categorical_coverage(table: DynamicTable, error_handler: ErrorHandler) -> list[dict[str, Any]]:
        """
        Report the values of a categorical column that its MeaningsTable does not annotate.

        Mirrors what hedtools reports during assembled validation (``SIDECAR_KEY_MISSING``, a warning), so
        the two modes agree. A MeaningsTable without a HED column carries no HED and is not checked.
        """
        issues = []
        for meanings in table.meanings_tables.values():
            if "HED" not in meanings.colnames:
                continue
            column = meanings.target
            levels = [str(value) for value in meanings["value"].data[:]]
            present = list(_distinct_values(column.data[:]))
            missing = [value for value in present if value not in levels]
            if not missing:
                continue
            error_handler.push_error_context(ErrorContext.COLUMN, column.name)
            try:
                issues += error_handler.format_error_with_context(
                    ValidationErrors.SIDECAR_KEY_MISSING,
                    invalid_keys=str(missing),
                    category_keys=levels,
                    column_name=column.name,
                )
            finally:
                error_handler.pop_error_context()
        return issues

    def _validate_once(self, annotation: str, rows: list[int], error_handler: ErrorHandler) -> list[dict[str, Any]]:
        """Validate one annotation under the ROW context of the first row holding it; stamp the row count."""
        error_handler.push_error_context(ErrorContext.ROW, rows[0])
        try:
            hed_obj = HedString(annotation, self.hed_schema, def_dict=self.def_dict)
            issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
        finally:
            error_handler.pop_error_context()
        for issue in issues:
            issue[ROW_COUNT_KEY] = len(rows)
        return issues

    @staticmethod
    def _unused_categorical_level_issues(sidecar_issues, df, json_data):
        """Return the sidecar issues for categorical levels that do not occur in the data.

        TabularInput validates only values present in the data, so a bad HED annotation on a
        categorical level that is never used would be missed. Those sidecar issues are added back.
        Value-column (template) and data-column errors are excluded because TabularInput reports them.
        """
        extra = []
        for issue in sidecar_issues:
            col = issue.get(ErrorContext.SIDECAR_COLUMN_NAME)
            key = issue.get(ErrorContext.SIDECAR_KEY_NAME)
            if not col or key is None or col not in df.columns:
                continue
            if "Levels" not in json_data.get(col, {}):  # only categorical columns have levels
                continue
            present = {str(v) for v in df[col].tolist()}
            if str(key) not in present:
                extra.append(issue)
        return extra

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
        Validates the annotations of a HedTags column one cell at a time, in isolation.

        This checks each HED string on its own. It does not see the other columns of the row, the
        categorical HED of a MeaningsTable, or the other rows, so use ``validate_table`` for a table.

        Parameters:
            hed_tags (HedTags): The HedTags column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            list[dict[str, Any]]: A list of validation issues found in the HedTags column

        Notes:
            An annotation that has already been validated in this column and found to have no issues
            is not validated again on the rows that repeat it. Such a row contributes nothing to the
            result, so the issues returned are the same as if every row were validated. A row whose
            annotation does have issues is still validated, so that each affected row is reported.
        """
        if hed_tags is None or not isinstance(hed_tags, HedTags):
            raise ValueError("The provided hed_tags is not a valid HedTags instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        issues = []
        validated_without_issues = set()

        # Slice once: on a file-backed column, iterating the dataset directly is one HDF5 read per row.
        # For an in-memory list the slice is a shallow copy of references (about 4 ms and 8 MB per
        # million rows, the cost of validating a few rows); for a numpy array it is a view.
        for index, tag in enumerate(hed_tags.data[:]):
            if tag is None or tag == "" or tag == "n/a" or tag in validated_without_issues:
                continue

            error_handler.push_error_context(ErrorContext.ROW, index)
            try:
                hed_obj = HedString(tag, self.hed_schema, def_dict=self.def_dict)
                row_issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
            finally:
                error_handler.pop_error_context()
            issues += row_issues

            if not row_issues:
                validated_without_issues.add(tag)

        return issues

    def validate_value_vector(
        self, hed_values: HedValueVector, error_handler: ErrorHandler | None = None
    ) -> list[dict[str, Any]]:
        """
        Validates a HedValueVector column in isolation: the template, then each substituted value.

        This checks the template and each substituted string on their own; use ``validate_table`` for
        a table.

        Parameters:
            hed_values (HedValueVector): The HedValueVector column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            list[dict[str, Any]]: A list of validation issues found in the HedValueVector column

        Notes:
            As in validate_vector, a substituted annotation that has already been validated in this
            column and found to have no issues is not validated again on the rows that repeat it.
        """
        if hed_values is None or not isinstance(hed_values, HedValueVector) or hed_values.hed is None:
            raise ValueError("The provided hed_values is not a valid HedValueVector instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)

        issues = []
        # Validate the HED template first
        hed_template = HedString(hed_values.hed, self.hed_schema, def_dict=self.def_dict)
        issues += hed_template.validate(allow_placeholders=True, error_handler=error_handler)
        if check_for_any_errors(issues):
            return issues

        validated_without_issues = set()
        # Slice once: on a file-backed column, iterating the dataset directly is one HDF5 read per row.
        # For an in-memory list the slice is a shallow copy of references (about 4 ms and 8 MB per
        # million rows, the cost of validating a few rows); for a numpy array it is a view.
        for index, tag in enumerate(hed_values.data[:]):
            if tag is None or tag == "" or tag == "n/a" or (isinstance(tag, float) and math.isnan(tag)):
                continue

            # Substitute the tag value into the template in place of #
            eval_tag = hed_values.hed.replace("#", str(tag))
            if eval_tag in validated_without_issues:
                continue

            error_handler.push_error_context(ErrorContext.ROW, index)
            try:
                hed_obj = HedString(eval_tag, self.hed_schema, def_dict=self.def_dict)
                row_issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
            finally:
                error_handler.pop_error_context()
            issues += row_issues

            if not row_issues:
                validated_without_issues.add(eval_tag)

        return issues


# ----------------------------------------------------------------------------------------------
# Module helpers


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
    """Map each distinct non-missing value, as text, to the rows holding it. Missing is None, NaN, "", "n/a"."""
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


def _shift_rows(issues: list[dict[str, Any]], offset: int) -> None:
    """Add offset to the ROW context of every issue that has an integer one."""
    for issue in issues:
        row = issue.get(ErrorContext.ROW)
        if isinstance(row, int) and not isinstance(row, bool):
            issue[ErrorContext.ROW] = row + offset
