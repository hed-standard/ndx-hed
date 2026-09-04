import json
import io
import math
import pandas as pd
import numpy as np
from typing import Union
from hed.models import Sidecar
from hed.schema import HedSchema, HedSchemaGroup
from pynwb.core import DynamicTable, VectorData
from pynwb.event import EventsTable, TimestampVectorData, DurationVectorData
from hdmf.common import MeaningsTable
from ndx_hed import HedLabMetaData, HedTags, HedValueVector

# Sidecar key under which the HedLabMetaData definitions are exported. In BIDS, definitions live in
# a sidecar entry that names no actual column; "definitions" is the conventional name for it.
DEFINITIONS_KEY = "definitions"


def extract_definitions(sidecar_data: dict, hed_schema: Union[HedSchema, HedSchemaGroup]) -> tuple:
    """
    Extracts definitions from a HED sidecar JSON data using the provided HED schema.

    Args:
        sidecar_data (dict): A dictionary representing the loaded HED Sidecar JSON data.
        hed_schema (HedSchema or HedSchemaGroup): The HED schema object for validation and processing.

    Returns:
        tuple: A tuple containing:
            - DefinitionDict: A dictionary of definitions extracted from the sidecar.
            - list: A list of validation issues found during extraction.
    """
    sidecar = Sidecar(io.StringIO(json.dumps(sidecar_data)))
    definitions = sidecar.get_def_dict(hed_schema)
    issues = sidecar._extract_definition_issues
    return definitions, issues


def extract_meanings(sidecar_data: dict) -> dict:
    """
    Converts a HED sidecar JSON data to a meanings dictionary.

    Args:
        sidecar_data (dict): A dictionary representing the loaded HED Sidecar JSON data.

    Returns:
        dict: A meanings dictionary with keys "categorical" and "value"
              - "categorical": dict mapping column names to their raw sidecar column-info dict
                (Levels and/or HED). A MeaningsTable cannot be built here because, as of
                PyNWB 4.0.0, a MeaningsTable requires the target VectorData column object; the
                MeaningsTable is created later in get_events_table once the column exists.
              - "value": dict mapping column names to HED strings
    """

    meanings = {"categorical": {}, "value": {}}

    for column_name, column_info in sidecar_data.items():
        if "Levels" in column_info or ("HED" in column_info and isinstance(column_info.get("HED", None), dict)):
            meanings["categorical"][column_name] = column_info
        elif "HED" in column_info:
            meanings["value"][column_name] = column_info["HED"]
    return meanings


def get_categorical_meanings(target_column: "VectorData", column_info: dict) -> "MeaningsTable":
    """
    Converts a categorical column info dict to a MeaningsTable annotating a target column.

    As of PyNWB 4.0.0, a MeaningsTable is bound to the VectorData column it annotates and its
    name is derived automatically as "{target_column.name}_meanings".

    Args:
        target_column (VectorData): The column object this MeaningsTable annotates. Must already
            be a column of the DynamicTable that the MeaningsTable will be added to.
        column_info (dict): The column info dictionary from the sidecar (Levels and/or HED).

    Returns:
        MeaningsTable: The constructed MeaningsTable object (name "{target_column.name}_meanings").
    """
    column_name = target_column.name
    description = column_info.get("Description", f"Meanings for {column_name}")
    meanings_tab = MeaningsTable(target=target_column, description=description)
    levels = column_info.get("Levels", {})  # Default to empty dict

    # Only a dict-valued HED provides per-category annotations. A string HED is a column-wide value
    # annotation (handled elsewhere as a HedValueVector), not categorical, so ignore it here.
    hed_info = column_info.get("HED", None)
    if not isinstance(hed_info, dict):
        hed_info = None

    # Determine the set of categories: prefer the Levels keys; otherwise fall back to the HED dict
    # keys so per-category HED is not dropped when Levels is absent.
    if levels:
        values = list(levels.keys())
    elif hed_info is not None:
        values = list(hed_info.keys())
    else:
        values = []

    hed_data = []
    for value in values:
        meanings_tab.add_row(value=value, meaning=levels.get(value, f"Description for {value}"))
        if hed_info is not None:
            hed_data.append(hed_info.get(value, "n/a"))
    if hed_info is not None:
        meanings_tab.add_column(
            name="HED", description=f"HED tags for {column_name} categories", col_cls=HedTags, data=hed_data
        )
    return meanings_tab


def get_events_table(name: str, description: str, df: pd.DataFrame, meanings: dict) -> "EventsTable":
    """
    Converts a pandas DataFrame and meanings dictionary to an EventsTable.

    Parameters:
        name (str): The name of the EventsTable.
        description (str): The description of the EventsTable.
        df (pd.DataFrame): The DataFrame containing event data.
        meanings (dict): The meanings dictionary with keys "categorical" and "value". The
            "categorical" values are raw sidecar column-info dicts (see extract_meanings).

    Returns:
        EventsTable: The constructed EventsTable object. Categorical columns are stored as plain
        VectorData columns, each annotated by a MeaningsTable attached to the table.
    """

    columns = []

    # Replace "n/a" with NaN in onset and duration columns directly in DataFrame
    if "onset" in df.columns:
        df["onset"] = df["onset"].replace(["n/a", "N/A", "na", "NA"], np.nan).infer_objects(copy=False)
    if "duration" in df.columns:
        df["duration"] = df["duration"].replace(["n/a", "N/A", "na", "NA"], np.nan).infer_objects(copy=False)

    # Add columns from the DataFrame
    for col_name in df.columns:
        col_data = df[col_name].tolist()
        if col_name == "onset":
            columns.append(TimestampVectorData(name="timestamp", description="Onset times of events", data=col_data))
        elif col_name == "duration":
            columns.append(DurationVectorData(name="duration", description="Duration of events", data=col_data))
        elif col_name in meanings["categorical"]:
            # A categorical column is a plain VectorData column; its MeaningsTable is attached to
            # the table after it is built (see below).
            columns.append(VectorData(name=col_name, description=f"Categorical column {col_name}", data=col_data))
        elif col_name in meanings["value"]:
            columns.append(
                HedValueVector(
                    name=col_name,
                    description=f"Value column {col_name}",
                    data=col_data,
                    hed=meanings["value"][col_name],
                )
            )
        elif col_name == "HED":
            columns.append(HedTags(name="HED", description="HED tags for events", data=col_data))
        else:
            columns.append(VectorData(name=col_name, description=f"Value column {col_name}", data=col_data))
    events_tab = EventsTable(name=name, description=description, columns=columns)
    # Attach a MeaningsTable to each categorical column now that the columns exist in the table.
    for col_name, column_info in meanings["categorical"].items():
        if col_name in events_tab:
            meanings_tab = get_categorical_meanings(events_tab[col_name], column_info)
            events_tab.add_meanings_table(meanings_tab)
    return events_tab


def _get_meanings_table(table: DynamicTable, col_name: str) -> Union["MeaningsTable", None]:
    """
    Returns the MeaningsTable annotating a column of a table, or None if the column has none.

    Prefers the public DynamicTable.get_meanings_for_column() API (it raises KeyError when the
    column has no MeaningsTable); falls back to the meanings_tables dict if the API is unavailable.

    Args:
        table (DynamicTable): The table owning the column.
        col_name (str): The name of the column.

    Returns:
        MeaningsTable or None: The MeaningsTable annotating col_name, or None if there is none.
    """
    getter = getattr(table, "get_meanings_for_column", None)
    if getter is not None:
        try:
            return getter(col_name)
        except KeyError:
            return None
    return table.meanings_tables.get(f"{col_name}_meanings")


def _is_missing(value) -> bool:
    """
    Returns True if a HED value is missing (None, the empty string, or a NaN of any float width).

    The NaN test converts rather than checking isinstance(value, float): numpy's float32 and float16
    do not subclass Python's float (only float64 does), so an isinstance check would silently treat
    those NaNs as present.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):  # not a number at all, so not a NaN
        return False


def get_levels_and_hed(meanings_table: "MeaningsTable") -> tuple:
    """
    Extracts the BIDS "Levels" and "HED" dictionaries from a MeaningsTable without using pandas.

    Args:
        meanings_table (MeaningsTable): The MeaningsTable annotating a categorical column. Its
            "value" and "meaning" columns supply the levels; an optional HedTags column named
            "HED" supplies the per-value HED annotations.

    Returns:
        tuple: A tuple containing:
            - dict: Levels -- maps each value to its meaning (empty string if there is no meaning).
            - dict: HED -- maps each value to its HED string, omitting missing (None, NaN, or
              empty) annotations. Empty if the MeaningsTable has no HED column.
    """
    # Each column is sliced once rather than iterated, so a file-backed column costs one read.
    values = list(meanings_table["value"].data[:])
    meanings = list(meanings_table["meaning"].data[:]) if "meaning" in meanings_table.colnames else []
    hed_strings = list(meanings_table["HED"].data[:]) if "HED" in meanings_table.colnames else []

    levels = {}
    hed_dict = {}
    for index, value in enumerate(values):
        levels[value] = meanings[index] if index < len(meanings) else ""
        if index < len(hed_strings) and not _is_missing(hed_strings[index]):
            hed_dict[value] = hed_strings[index]
    return levels, hed_dict


def get_json_hed_dict(table: DynamicTable, hed_metadata: HedLabMetaData = None) -> dict:
    """
    Builds the BIDS-style JSON sidecar dictionary of a DynamicTable directly from its columns.

    This is the metadata half of get_bids_tabular(). It reads the column objects and the
    MeaningsTable annotating each categorical column, so it needs neither a dataframe nor pandas.

    Each entry maps a column name to a BIDS sidecar column-info dict, which may contain:
        - "Description": the column's description, if it has one.
        - "HED": for a HedValueVector, its value template (a string containing a single "#");
          for a categorical column, a dict mapping each value to its HED string.
        - "Levels": for a categorical column, a dict mapping each value to its meaning.

    Columns contribute as follows:
        - HedTags (the "HED" column): omitted entirely. Its cells are HED strings, so the column
          is self-describing, and "HED" is a reserved sidecar key that must not name an entry.
        - TimestampVectorData/DurationVectorData: description only, since the BIDS onset and
          duration columns carry no HED metadata. The entry keeps the column's own name, so an
          EventsTable "timestamp" column is keyed "timestamp" even though get_bids_tabular()
          renames it to "onset" in the dataframe.
        - HedValueVector: its HED template, unless the template is empty or "n/a".
        - Any other column: the Levels and HED of the MeaningsTable annotating it, if any.

    Columns with no metadata are omitted, so the result is empty for a table with no descriptions,
    no MeaningsTables, and no HED template columns.

    In NWB, HED definitions live in a HedLabMetaData object, which is the only place extra
    definitions may come from. When one is given, its definitions are exported under the
    "definitions" key as ``{"HED": {"defList": <definitions>}}`` -- a sidecar entry that names no
    column, which is how BIDS carries definitions. The resulting sidecar is then self-contained:
    the ``Def/`` references in the table can be resolved without supplying the definitions
    separately. If the HedLabMetaData holds no definitions, no entry is added.

    Parameters:
        table (DynamicTable): The table to extract the sidecar metadata from. As with
            get_bids_tabular(), this is not meant for a MeaningsTable, whose HED is consumed while
            assembling the table whose column it annotates.
        hed_metadata (HedLabMetaData, optional): The HED lab metadata supplying the definitions.
            If None (the default), the sidecar carries no definitions.

    Returns:
        dict: The JSON sidecar data with column metadata, levels, HED annotations, and definitions.

    Raises:
        ValueError: If hed_metadata is given but is not a HedLabMetaData instance.
        ValueError: If the definitions would overwrite the entry of a column named "definitions".
    """
    if hed_metadata is not None and not isinstance(hed_metadata, HedLabMetaData):
        raise ValueError(
            "The hed_metadata must be a HedLabMetaData instance -- in NWB it is the only source of "
            f"extra HED definitions, but {type(hed_metadata).__name__} was given."
        )

    json_data = {}

    for col_name in table.colnames:
        column = table[col_name]
        column_info = {}

        # Add description if available
        if hasattr(column, "description") and column.description:
            column_info["Description"] = column.description

        # Handle different column types
        if isinstance(column, (TimestampVectorData, DurationVectorData)):
            # The BIDS onset and duration columns don't carry HED metadata.
            # TODO: Might need to extend the duration column to include a HED field if needed.
            pass

        elif isinstance(column, HedTags):
            # The HED column is self-describing (its cells are HED strings). "HED" is a reserved
            # sidecar key and must NOT appear as a sidecar metadata entry, so emit nothing for it.
            continue

        elif isinstance(column, HedValueVector):
            if column.hed != "" and column.hed != "n/a":
                column_info["HED"] = column.hed

        else:
            # A categorical column is a plain VectorData annotated by a MeaningsTable.
            meanings_table = _get_meanings_table(table, col_name)
            if meanings_table is not None:
                levels, hed_dict = get_levels_and_hed(meanings_table)
                if levels:
                    column_info["Levels"] = levels
                if hed_dict:
                    column_info["HED"] = hed_dict

        # Add column info to JSON if it has any metadata
        if column_info:
            json_data[col_name] = column_info

    # Export the definitions from the HedLabMetaData -- the only source of extra HED definitions
    definitions = hed_metadata.definitions if hed_metadata is not None else None
    if definitions:
        if DEFINITIONS_KEY in json_data:
            raise ValueError(
                f"Table '{table.name}' has a column named '{DEFINITIONS_KEY}', which collides with the "
                f"sidecar key used to export the HED definitions. Rename the column to export definitions."
            )
        json_data[DEFINITIONS_KEY] = {"HED": {"defList": definitions}}

    return json_data


def get_bids_tabular(table: DynamicTable, hed_metadata: HedLabMetaData = None) -> tuple:
    """
    Converts a DynamicTable to a BIDS-style tabular representation (DataFrame and JSON sidecar).

    Works for any DynamicTable (an EventsTable or a plain DynamicTable). It is not meant for a
    MeaningsTable, whose HED is consumed while assembling the table whose column it annotates. A
    ``TimestampVectorData`` column is renamed to ``onset`` so that downstream BIDS-HED validation
    treats the table as a timeline (temporal) file.

    Parameters:
        table (DynamicTable): The table to convert.
        hed_metadata (HedLabMetaData, optional): The HED lab metadata supplying the definitions,
            passed through to get_json_hed_dict(). If None (the default), the sidecar carries no
            definitions and any ``Def/`` references in the table cannot be resolved from it alone.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The table data with BIDS column names (onset, duration, etc.)
            - dict: The JSON sidecar data as returned by get_json_hed_dict().
    """

    # Get DataFrame from the table
    df = table.to_dataframe()

    # Rename the timestamp column back to onset so the table reads as a BIDS timeline file. The
    # "timestamp" column must itself be a TimestampVectorData -- an unrelated column that merely
    # happens to be named "timestamp" is left alone.
    if "timestamp" in table.colnames and isinstance(table["timestamp"], TimestampVectorData):
        df = df.rename(columns={"timestamp": "onset"})

    return df, get_json_hed_dict(table, hed_metadata)
