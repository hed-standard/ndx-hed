"""
Convert hed-tests JSON validation cases to NWB objects.

The hed-tests suite (``spec_tests/hed-tests/json_test_data/validation_tests.json``) describes each
case as BIDS content: a sidecar dict, an events table given as a header row plus data rows, or both.
The functions here build the NWB objects a user following the ndx-hed documentation would create
for that content, using the library's own converters (``extract_meanings``, ``get_events_table``,
``get_categorical_meanings``) wherever one exists, so that the spec tests exercise the converters
as well as the validator. Only two shapes have no library converter and are built here directly:
a sidecar with no events (a zero-row table) and an events table without an ``onset`` column (a
plain ``DynamicTable`` rather than an ``EventsTable``).

The mapping rules are numbered M1-M7 in ``spec_tests/README.md``.
"""

from datetime import datetime, timezone

import pandas as pd
from pynwb import NWBFile
from pynwb.core import DynamicTable, VectorData

from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.bids2nwb import extract_meanings, get_categorical_meanings, get_events_table

HED_KEY = "HED"
LEVELS_KEY = "Levels"
DEFINITION_MARKER = "Definition/"
EMPTY_MEANINGS = {"categorical": {}, "value": {}}


def schema_version_string(schema) -> str:
    """Return the record's ``schema`` field as the single string HedLabMetaData takes (M1).

    A list is joined with commas, which hedtools accepts when every version shares one namespace.
    A list mixing namespaces (``['8.5.0', 'sc:testconflict_2.1.0']``) cannot be expressed this way;
    HedLabMetaData then fails to load it and the harness skips the record.
    """
    if isinstance(schema, list):
        return ",".join(str(version).strip() for version in schema)
    return str(schema).strip()


def join_definitions(*definition_lists) -> str | None:
    """Join one or more lists of definition strings into the single string HedLabMetaData takes (M1)."""
    definitions = [text for group in definition_lists if group for text in group]
    if not definitions:
        return None
    return ", ".join(definitions)


def has_hed(entry) -> bool:
    """Return True if a sidecar entry carries HED or Levels (so it needs a column in NWB)."""
    return isinstance(entry, dict) and (HED_KEY in entry or LEVELS_KEY in entry)


def is_definitions_entry(entry) -> bool:
    """Return True if a sidecar entry is a definitions holder (M5).

    That is a categorical-shaped entry (dict-valued ``HED``) each of whose values contains
    ``Definition/``. The test is "contains", not "is a well-formed definition group": the
    DEFINITION_INVALID cases are malformed on purpose, and HedLabMetaData rejects them at
    construction, which is the expected outcome for those cases.
    """
    if not isinstance(entry, dict):
        return False
    hed = entry.get(HED_KEY)
    if not isinstance(hed, dict) or not hed:
        return False
    return all(isinstance(value, str) and DEFINITION_MARKER in value for value in hed.values())


def split_definition_entries(sidecar: dict, header: list | None = None) -> tuple[dict, list[str]]:
    """Separate definitions-holder entries from the sidecar (M5).

    Parameters:
        sidecar (dict): The BIDS sidecar of the case.
        header (list or None): The events header, or None for a sidecar-only case. A definitions
            entry is folded only when its column is absent from the header (always, when there is
            no header), since a column that exists in the events must stay a column.

    Returns:
        tuple: (sidecar without the folded entries, list of definition strings in sidecar order)
    """
    remaining = {}
    definitions = []
    for column, entry in sidecar.items():
        absent = header is None or column not in header
        if absent and is_definitions_entry(entry):
            definitions.extend(entry[HED_KEY].values())
        else:
            remaining[column] = entry
    return remaining, definitions


def absent_hed_columns(sidecar: dict, header: list) -> list[str]:
    """Return the HED-bearing sidecar columns that the events header lacks (M6).

    hedtools validates such an entry anyway; NWB has no place for it because HED attaches only to
    a column that exists. The harness skips a case that has any.
    """
    return [column for column, entry in sidecar.items() if has_hed(entry) and column not in header]


def is_ragged(rows: list) -> bool:
    """Return True if any data row has a different length from the header row."""
    width = len(rows[0])
    return any(len(row) != width for row in rows[1:])


def build_metadata(schema, definitions, extra_definitions=()) -> HedLabMetaData:
    """Build the HedLabMetaData for a case (M1).

    Raises:
        ValueError: From HedLabMetaData when the schema cannot be loaded or a definition is invalid.
            The harness tells the two apart by the message prefix (see ``SCHEMA_LOAD_PREFIX``).
    """
    return HedLabMetaData(
        hed_schema_version=schema_version_string(schema),
        definitions=join_definitions(definitions, list(extra_definitions)),
    )


# HedLabMetaData raises ValueError with this prefix when the schema itself cannot be loaded
# (hed_lab_metadata.py, _init_internal); any other ValueError from it is a definition problem.
SCHEMA_LOAD_PREFIX = "Failed to load HED schema version"


def build_sidecar_table(sidecar: dict, name: str = "sidecar_only") -> DynamicTable | None:
    """Build the zero-row DynamicTable for a sidecar-only case (M2).

    Each dict-``HED`` (or ``Levels``) entry becomes an empty VectorData column with a MeaningsTable
    built by ``get_categorical_meanings``; each string-``HED`` entry becomes an empty HedValueVector
    carrying the template; a description-only entry becomes an empty VectorData. Sidecar.validate
    checks every level and template whether or not rows use them, so zero rows lose nothing.

    Returns:
        DynamicTable or None: None when the sidecar has no entries left (for example when every entry
        was a definitions holder folded into the metadata).

    Raises:
        ValueError: From HedValueVector when a template does not contain exactly one ``#``.
    """
    columns = []
    categorical = {}
    for column_name, entry in sidecar.items():
        if not isinstance(entry, dict):
            continue
        description = entry.get("Description", f"Column {column_name}")
        hed = entry.get(HED_KEY)
        if isinstance(hed, dict) or LEVELS_KEY in entry:
            columns.append(VectorData(name=column_name, description=description, data=[]))
            categorical[column_name] = entry
        elif isinstance(hed, str):
            columns.append(HedValueVector(name=column_name, description=description, data=[], hed=hed))
        else:
            columns.append(VectorData(name=column_name, description=description, data=[]))
    if not columns:
        return None
    table = DynamicTable(name=name, description="Zero-row table built from a hed-tests sidecar case", columns=columns)
    for column_name, entry in categorical.items():
        table.add_meanings_table(get_categorical_meanings(table[column_name], entry))
    return table


def build_events_table(
    rows: list, meanings: dict | None = None, name: str = "events", description: str = ""
) -> DynamicTable:
    """Build the table for an events or combo case (M3, M4).

    Parameters:
        rows (list): The header row followed by the data rows, as in the JSON.
        meanings (dict or None): The ``extract_meanings`` result for the case's sidecar, or None for
            an events-only case.
        name (str): The table name.
        description (str): The table description.

    Returns:
        DynamicTable: An EventsTable from ``get_events_table`` when the header has an ``onset`` column
        (so the table is validated as a timeline), otherwise a plain DynamicTable built with the same
        column rules: ``HED`` -> HedTags, a value column -> HedValueVector, a categorical column ->
        VectorData with a MeaningsTable, anything else -> VectorData.

    Raises:
        ValueError: From pandas for ragged rows (check ``is_ragged`` first) or from HedValueVector for
            a template without exactly one ``#``.
    """
    if meanings is None:
        meanings = EMPTY_MEANINGS
    header = list(rows[0])
    df = pd.DataFrame(rows[1:], columns=header)
    description = description or "Table built from a hed-tests case"
    if "onset" in header:
        return get_events_table(name, description, df, meanings)

    columns = []
    for column_name in header:
        data = df[column_name].tolist()
        if column_name in meanings["categorical"]:
            columns.append(VectorData(name=column_name, description=f"Categorical column {column_name}", data=data))
        elif column_name in meanings["value"]:
            columns.append(
                HedValueVector(
                    name=column_name,
                    description=f"Value column {column_name}",
                    data=data,
                    hed=meanings["value"][column_name],
                )
            )
        elif column_name == HED_KEY:
            columns.append(HedTags(name=HED_KEY, description="HED tags", data=data))
        else:
            columns.append(VectorData(name=column_name, description=f"Column {column_name}", data=data))
    table = DynamicTable(name=name, description=description, columns=columns)
    for column_name, entry in meanings["categorical"].items():
        if column_name in table.colnames:
            table.add_meanings_table(get_categorical_meanings(table[column_name], entry))
    return table


def build_combo_table(sidecar: dict, rows: list, name: str = "events") -> DynamicTable:
    """Build the table for a combo case from its (already M5-split) sidecar and events (M4)."""
    return build_events_table(rows, extract_meanings(sidecar), name=name)


def build_nwbfile(metadata: HedLabMetaData, table: DynamicTable | None, identifier: str = "hed-tests") -> NWBFile:
    """Put the metadata and the table (if any) in a fresh NWBFile ready for ``validate_file``."""
    nwbfile = NWBFile(
        session_description="hed-tests validation case",
        identifier=identifier,
        session_start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    nwbfile.add_lab_meta_data(metadata)
    if table is not None:
        nwbfile.add_acquisition(table)
    return nwbfile
