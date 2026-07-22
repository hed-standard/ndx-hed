"""
HedValidator class for validating HED tags in NWB DynamicTable objects.
"""

import io
import json
import math
from typing import List, Dict, Any, Optional
from pynwb import NWBFile
from pynwb.core import DynamicTable
from pynwb.event import EventsTable
from hdmf.common import MeaningsTable
from hed.errors import ErrorHandler, ErrorContext, HedExceptions, HedFileError
from hed.errors.error_reporter import check_for_any_errors
from hed.models import HedString, TabularInput, Sidecar
from ..hed_lab_metadata import HedLabMetaData
from ..hed_tags import HedTags, HedValueVector
from .bids2nwb import get_bids_tabular


class HedNWBValidator:
    """
    A validator class for HED tags in NWB DynamicTable objects.

    This class provides methods to validate HED tags in various NWB data structures
    using HED schema information stored in HedLabMetaData.
    """

    # Sidecar error codes that indicate a structurally malformed sidecar (bad ``{column}`` braces or
    # an otherwise invalid sidecar). These are only detected by Sidecar.validate(); when present, the
    # assembled-table validation would emit misleading downstream errors, so it is skipped.
    STRUCTURAL_SIDECAR_CODES = frozenset({"SIDECAR_BRACES_INVALID", "SIDECAR_INVALID"})

    def __init__(self, hed_metadata: HedLabMetaData):
        """
        Initialize the HedNWBValidator with HED metadata.

        Parameters:
            hed_metadata (HedLabMetaData): The HED lab metadata containing schema information.
                                          Must be a valid HedLabMetaData instance with a loaded
                                          HED schema. If the HedLabMetaData was constructed successfully,
                                          it is guaranteed to have a valid schema.

        Raises:
            ValueError: If hed_metadata is not an instance of HedLabMetaData

        Notes:
            HedLabMetaData validates the schema during its own construction, so if a
            HedLabMetaData instance exists, it is guaranteed to have a valid HED schema
            and version. No additional validation is needed here.
        """
        if not isinstance(hed_metadata, HedLabMetaData):
            raise ValueError("hed_metadata must be an instance of HedLabMetaData")

        self.hed_schema = hed_metadata.get_hed_schema()
        self.def_dict = hed_metadata.get_definition_dict()

    def validate_table(self, table: DynamicTable, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates all HedTags columns in a DynamicTable using the provided HED schema metadata.

        Parameters:
            table (DynamicTable): The dynamic table to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            List[Dict[str, Any]]: A consolidated list of validation issues from all HedTags columns
        """
        if table is None or not isinstance(table, DynamicTable):
            raise ValueError("The provided table is not a valid DynamicTable instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        issues = []
        # TODO: FILE_NAME context needs to be replaced by TABLE context when available in hed-python
        error_handler.push_error_context(ErrorContext.FILE_NAME, table.name)
        for col in table.columns:
            if isinstance(col, HedTags):
                error_handler.push_error_context(ErrorContext.COLUMN, col.name)
                col_issues = self.validate_vector(col, error_handler)
                issues += col_issues
                error_handler.pop_error_context()
            elif isinstance(col, HedValueVector):
                error_handler.push_error_context(ErrorContext.COLUMN, col.name)
                col_issues = self.validate_value_vector(col, error_handler)
                issues += col_issues
                error_handler.pop_error_context()

        error_handler.pop_error_context()
        return issues

    def validate_vector(self, hed_tags: HedTags, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates a HedTags column using the provided HED schema metadata.

        Parameters:
            hed_tags (HedTags): The HedTags column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            List[Dict[str, Any]]: A list of validation issues found in the HedTags column
        """
        if hed_tags is None or not isinstance(hed_tags, HedTags):
            raise ValueError("The provided hed_tags is not a valid HedTags instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        issues = []

        for index, tag in enumerate(hed_tags.data):
            if tag is None or tag == "" or tag == "n/a":
                continue

            error_handler.push_error_context(ErrorContext.ROW, index)
            hed_obj = HedString(tag, self.hed_schema, def_dict=self.def_dict)
            row_issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
            issues += row_issues
            error_handler.pop_error_context()

        return issues

    def validate_value_vector(
        self, hed_values: HedValueVector, error_handler: Optional[ErrorHandler] = None
    ) -> List[Dict[str, Any]]:
        """
        Validates a HedValueVector column using the provided HED schema metadata.

        Parameters:
            hed_values (HedValueVector): The HedValueVector column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            List[Dict[str, Any]]: A list of validation issues found in the HedValueVector column
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

        for index, tag in enumerate(hed_values.data):
            if tag is None or tag == "" or tag == "n/a" or (isinstance(tag, float) and math.isnan(tag)):
                continue

            error_handler.push_error_context(ErrorContext.ROW, index)
            # Substitute the tag value into the template in place of #
            eval_tag = hed_values.hed.replace("#", str(tag))
            hed_obj = HedString(eval_tag, self.hed_schema, def_dict=self.def_dict)
            row_issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
            issues += row_issues
            error_handler.pop_error_context()
        return issues

    def validate_events(
        self, events: EventsTable, error_handler: Optional[ErrorHandler] = None
    ) -> List[Dict[str, Any]]:
        """
        Validates HED tags in an EventsTable by converting it to BIDS format and validating the events.

        This function extracts the BIDS-formatted DataFrame and JSON sidecar from the EventsTable
        using get_bids_tabular(), then validates the HED tags contained within using the provided
        HED schema metadata.

        Parameters:
            events (EventsTable): The EventsTable to validate containing HED tags
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            List[Dict[str, Any]]: A list of validation issues found in the EventsTable HED tags

        Raises:
            ValueError: If the EventsTable is invalid or cannot be converted to BIDS format

        Notes:
            This function uses get_bids_tabular() to extract BIDS-formatted data from the EventsTable,
            then applies HED validation to the extracted event annotations. The validation follows
            BIDS-HED standards for event annotation validation.
        """
        if events is None or not isinstance(events, EventsTable):
            raise ValueError("The provided events is not a valid EventsTable instance.")

        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)

        return self._validate_assembled(events, error_handler)

    def _validate_assembled(self, table: DynamicTable, error_handler: ErrorHandler) -> List[Dict[str, Any]]:
        """
        Assembled (BIDS-style) validation of a DynamicTable.

        The table is converted to a BIDS-format dataframe + JSON sidecar with get_bids_tabular().
        The sidecar (column metadata: value templates and categorical Levels/HED) is validated first
        with Sidecar.validate(), then the assembled per-row annotations are validated with
        TabularInput.validate(). Both steps are required: TabularInput.validate() does NOT re-run the
        sidecar's brace-structure / column-reference checks (self, nested, invalid, or malformed
        ``{column}`` references), so a malformed sidecar validated only through the assembled table
        would be missed and surface as misleading downstream errors (e.g. a stray ``{`` reported as
        CHARACTER_INVALID). If the sidecar itself has errors, they are returned and the assembled-table
        step is skipped to avoid that downstream noise.

        Assembly combines, for each row, the row's direct HED column, its categorical HED (from
        attached MeaningsTables), and its value-template HED into a single annotation. If the assembled
        dataframe has an ``onset`` column, TabularInput performs temporal (timeline) validation;
        otherwise it performs non-temporal (per-row) validation.

        Parameters:
            table (DynamicTable): The table to validate.
            error_handler (ErrorHandler): The error handler collecting issues.

        Returns:
            List[Dict[str, Any]]: Validation issues for the table.
        """
        df, json_data = get_bids_tabular(table)

        # No sidecar metadata: validate the assembled table on its own (e.g. only a direct HED column).
        if not json_data:
            tab_input = TabularInput(file=df, name=table.name)
            return tab_input.validate(self.hed_schema, extra_def_dicts=self.def_dict, error_handler=error_handler)

        # Step 1: validate the sidecar metadata explicitly. Only Sidecar.validate() performs the
        # brace-structure / column-reference checks; it also validates the HED of every categorical
        # level even those not present in the data.
        sidecar = Sidecar(io.StringIO(json.dumps(json_data)), name=table.name)
        sidecar_issues = sidecar.validate(self.hed_schema, extra_def_dicts=self.def_dict, error_handler=error_handler)
        for issue in sidecar_issues:
            if not issue.get("ec_filename"):
                issue["ec_filename"] = table.name

        # If the sidecar is structurally malformed (bad braces / invalid sidecar), the assembled-table
        # step would miss it and emit misleading downstream errors, so stop and report the structure.
        if any(issue.get("code") in self.STRUCTURAL_SIDECAR_CODES for issue in sidecar_issues):
            return sidecar_issues

        # Step 2: validate the assembled table. This carries full context (ec_filename / ec_column /
        # ec_row) and performs temporal (timeline) validation when an ``onset`` column is present. It
        # re-reports the categorical/value HED errors for values that occur in the data, so those are
        # taken from here (with context) rather than from the sidecar step.
        tab_input = TabularInput(file=df, sidecar=sidecar, name=table.name)
        issues = tab_input.validate(self.hed_schema, extra_def_dicts=self.def_dict, error_handler=error_handler)

        # TabularInput only sees categorical values that occur in the data, so add the sidecar errors
        # for categorical levels that never appear (otherwise they would be missed).
        issues += self._unused_categorical_level_issues(sidecar_issues, df, json_data)
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
            col = issue.get("ec_sidecarColumnName")
            key = issue.get("ec_sidecarKeyName")
            if not col or key is None or col not in df.columns:
                continue
            if "Levels" not in json_data.get(col, {}):  # only categorical columns have levels
                continue
            present = {str(v) for v in df[col].tolist()}
            if str(key) not in present:
                extra.append(issue)
        return extra

    def _check_meanings_table_rules(self, meanings_table: MeaningsTable) -> None:
        """
        Enforce structural rules on a MeaningsTable.

        A MeaningsTable carries categorical (per-value) HED in a HedTags column. A HedValueVector
        (a value template with a ``#`` placeholder) has no meaning for per-value categorical
        annotation and is not allowed in a MeaningsTable.

        Raises:
            ValueError: If the MeaningsTable contains a HedValueVector column.
        """
        for col in meanings_table.columns:
            if isinstance(col, HedValueVector):
                raise ValueError(
                    f"HedValueVector column '{col.name}' is not allowed in MeaningsTable "
                    f"'{meanings_table.name}'; categorical HED must be stored in a HedTags column."
                )

    def validate_file(self, nwbfile: NWBFile, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates all HED tags in an NWB file by iterating through all DynamicTable objects.

        This method first checks that HedLabMetaData is defined in the NWB file and that its schema
        version matches the validator's. Then it validates every DynamicTable **except MeaningsTable**
        using assembled (BIDS-style) validation (see _validate_assembled): the table is converted to a
        dataframe + sidecar and validated with TabularInput, which performs temporal (timeline)
        validation when the table has an ``onset`` column and non-temporal validation otherwise. A
        MeaningsTable is not validated on its own -- its categorical HED is validated as part of the
        table whose column it annotates -- but it is checked against the structural rule that it must
        not contain a HedValueVector column (a violation raises ValueError).

        Parameters:
            nwbfile (NWBFile): The NWB file to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors.
                                                   If None, a new instance will be created.

        Returns:
            List[Dict[str, Any]]: A consolidated list of validation issues from all tables in the file

        Raises:
            ValueError: If nwbfile is not a valid NWBFile instance
            ValueError: If a MeaningsTable contains a HedValueVector column
            HedFileError: If HedLabMetaData is missing or invalid in the NWB file
            HedFileError: If the HED schema version in the NWB file does not match the validator's schema version
        """
        if nwbfile is None or not isinstance(nwbfile, NWBFile):
            raise ValueError("The provided nwbfile is not a valid NWBFile instance.")

        # Check if HedLabMetaData is defined in the file and matches the validator's schema version
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
        # Validate every DynamicTable with assembled (BIDS-style) validation, except MeaningsTables.
        # A MeaningsTable is a lookup consumed during the assembly of the table whose column it
        # annotates, so it is not validated on its own; it is only checked against the structural
        # rule that it must not contain a HedValueVector column.
        for obj in nwbfile.all_children():
            if not isinstance(obj, DynamicTable):
                continue
            if isinstance(obj, MeaningsTable):
                self._check_meanings_table_rules(obj)  # raises ValueError on a disallowed column
                continue
            issues.extend(self._validate_assembled(obj, error_handler))
        error_handler.pop_error_context()
        return issues
