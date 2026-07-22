import json
import io
import pandas as pd
import numpy as np
from typing import Union
from hed.models import Sidecar
from hed.schema import HedSchema, HedSchemaGroup
from pynwb.core import DynamicTable, VectorData
from pynwb.event import EventsTable, TimestampVectorData, DurationVectorData
from hdmf.common import MeaningsTable
from ndx_hed import HedTags, HedValueVector


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


def get_bids_tabular(table: DynamicTable) -> tuple:
    """
    Converts a DynamicTable to a BIDS-style tabular representation (DataFrame and JSON sidecar).

    Works for any DynamicTable (an EventsTable or a plain DynamicTable). It is not meant for a
    MeaningsTable, whose HED is consumed while assembling the table whose column it annotates. A
    ``TimestampVectorData`` column is renamed to ``onset`` so that downstream BIDS-HED validation
    treats the table as a timeline (temporal) file.

    Parameters:
        table (DynamicTable): The table to convert.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The table data with BIDS column names (onset, duration, etc.)
            - dict: The JSON sidecar data with column metadata, levels, and HED annotations
    """

    # Get DataFrame from the table
    df = table.to_dataframe()

    # Initialize JSON sidecar structure
    json_data = {}

    # Process each column to build JSON metadata
    for col_name in table.colnames:
        column = table[col_name]
        column_info = {}

        # Add description if available
        if hasattr(column, "description") and column.description:
            column_info["Description"] = column.description

        # Handle different column types
        if isinstance(column, TimestampVectorData):
            # Rename timestamp back to onset in DataFrame
            if "timestamp" in df.columns:
                df = df.rename(columns={"timestamp": "onset"})
            # TimestampVectorData doesn't typically have HED metadata in BIDS

        elif isinstance(column, DurationVectorData):
            # Duration column - no special HED metadata typically
            # TODO: Might need to extend this to include a HED field if needed.
            pass

        elif isinstance(column, HedValueVector) and column.hed != "" and column.hed != "n/a":
            column_info["HED"] = column.hed

        elif isinstance(column, HedTags):
            # The HED column is self-describing (its cells are HED strings). "HED" is a reserved
            # sidecar key and must NOT appear as a sidecar metadata entry, so emit nothing for it.
            continue

        else:
            # A categorical column is a plain VectorData annotated by a MeaningsTable. Prefer the
            # public DynamicTable.get_meanings_for_column() API (it raises KeyError when the column
            # has no MeaningsTable); fall back to the meanings_tables dict if the API is unavailable.
            getter = getattr(table, "get_meanings_for_column", None)
            if getter is not None:
                try:
                    meanings_table = getter(col_name)
                except KeyError:
                    meanings_table = None
            else:
                meanings_table = table.meanings_tables.get(f"{col_name}_meanings")
            if meanings_table is not None:
                meanings_df = meanings_table.to_dataframe()

                # Build Levels dictionary
                levels = {}
                hed_dict = {}

                for _, row in meanings_df.iterrows():
                    value = row["value"]
                    meaning = row.get("meaning", "")
                    levels[value] = meaning

                    # Check for HED column
                    if "HED" in row and pd.notna(row["HED"]) and row["HED"] != "":
                        hed_dict[value] = row["HED"]

                if levels:
                    column_info["Levels"] = levels
                if hed_dict:
                    column_info["HED"] = hed_dict

        # Add column info to JSON if it has any metadata
        if column_info:
            json_data[col_name] = column_info

    return df, json_data
