# HED annotation and validation in ndx-hed

This document describes how HED (Hierarchical Event Descriptors) annotations are represented in NWB tables, the rules ndx-hed follows, and how the validator works. It reflects the 1.0.0 design (PyNWB 4.0.0, where EventsTable, MeaningsTable, and related types are part of NWB core).

## Representing HED in a table

There are three ways a column contributes HED to a table, mirroring the two BIDS sidecar forms:

- Per-row HED: a `HedTags` column stores one HED string per row.
- Value HED: a `HedValueVector` column stores one HED template containing a single `#` placeholder; the placeholder is replaced by each row's value to produce that row's annotation.
- Categorical HED: a plain column of category labels is annotated by a `MeaningsTable`, which maps each distinct value to a meaning and (optionally) a HED string held in a `HedTags` column named `HED` inside the MeaningsTable.

`MeaningsTable` is a core hdmf type. ndx-hed does not define it; ndx-hed carries categorical HED by adding a `HedTags` column to it.

## HED column rules

The following rules govern how HED may appear in an NWB table.

- Rule R1: A `HedTags` column must be named `HED`.
- Rule R2: A `DynamicTable` has at most one `HedTags` column.
- Rule R3: A `HedTags` column inside a `MeaningsTable` provides categorical (per-value) HED for the column that the MeaningsTable annotates.
- Rule R4: A `HedTags` column in any other `DynamicTable` provides per-row HED for that table.
- Rule R5: A `HedValueVector` must not appear in a `MeaningsTable`.
- Rule R6: A column named `HED`, in a `DynamicTable` or in a `MeaningsTable`, must be a `HedTags`. The name is what marks the column as HED (R3, R4), so a `VectorData` or a `HedValueVector` named `HED` is an error.
- Rule R7: The values of a `HedValueVector` must satisfy the value class of the `#` tag of its template. A `#` with no value class is `textClass`. When the template is `Def/Name/#`, the class is that of the placeholder tag inside the definition.

### How each rule is enforced

| Rule | How it is enforced                                                                                                                                                                                                                                                                              |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1   | `HedTags.__init__` raises `ValueError` if the name is not `HED` (which is also the default).                                                                                                                                                                                                    |
| R2   | Follows from R1: column names within a table are unique, so two `HED` columns cannot coexist.                                                                                                                                                                                                   |
| R3   | The MeaningsTable's `HED` column is consumed as categorical HED when assembling the annotated table.                                                                                                                                                                                            |
| R4   | The table's `HED` column is assembled as its per-row HED.                                                                                                                                                                                                                                       |
| R5   | `HedNWBValidator.validate_table` reports `MEANINGS_VALUE_VECTOR_INVALID` and stops validating that table.                                                                                                                                                                                       |
| R6   | `HedNWBValidator.validate_table` reports `HED_COLUMN_TYPE_INVALID` and stops validating that table.                                                                                                                                                                                             |
| R7   | `HedNWBValidator.validate_table` checks the column against the class (a numeric column under a numeric or text class, or an integer column under a name class, passes on its dtype alone; otherwise each distinct value is substituted into the template and validated) and stops on any error. |

Notes:

- `HedValueVector` may have any column name and is identified by its neurodata type, not by name.
- `MEANINGS_VALUE_VECTOR_INVALID` and `HED_COLUMN_TYPE_INVALID` are ndx-hed codes, registered with hedtools so the issues have the same shape as hedtools' own (`code`, `message`, `severity`, and the `ec_*` context keys). R7 errors are hedtools codes (`VALUE_INVALID`, `CHARACTER_INVALID`, and whatever else the substituted string fails).
- The `HedValueVector` schema documentation previously stated "Always has the name HED"; that was incorrect and has been corrected.

## How validation works

HED is not validated only tag-by-tag. Its meaning depends on the other HED in the same row, and for time-anchored tables on the other rows. `HedNWBValidator.validate_table` is the table validator; `HedNWBValidator.validate_file` finds the file's `HedLabMetaData` and calls `validate_table` for every `DynamicTable` in the file except a `MeaningsTable`, whose HED is validated with the table it annotates. Passing a `MeaningsTable` to `validate_table` raises `ValueError`.

### The steps of `validate_table`

"Stops" means the issues found so far for that table are returned; the other tables of a file are still validated.

1. Structural rules R5 and R6 on the table and its MeaningsTables. An issue stops.
2. A table with no `HedTags` column, no `HedValueVector` column, and no MeaningsTable with a `HED` column has nothing to validate and returns no issues without being read. A file's large HED-free tables (a Units table) cost nothing.
3. The table's column metadata becomes a BIDS sidecar dict with `get_json_hed_dict`: the `HedValueVector` templates, the categorical `Levels` and `HED` of each MeaningsTable, and the definitions of the `HedLabMetaData` under the `definitions` key. No table data is read.
4. The sidecar is validated with hedtools `Sidecar.validate`. Only this step performs the brace-structure and column-reference checks (self, nested, invalid, or malformed `{column}` references) and validates the HED of every categorical level, used or not. Any error stops: a sidecar-level error would be repeated on every row that uses it, and the row annotations assembled from it cannot be trusted. Warnings do not stop.
5. Rule R7 on every `HedValueVector` column. Any error stops.
6. The assembly gate:
   - `assemble=True` (the default): the whole table is read into a BIDS dataframe with `get_bids_dataframe` (a `TimestampVectorData` column becomes `onset`; missing cells become `n/a`) and hedtools `TabularInput.validate` runs. It checks each cell on its own, each categorical value against its levels, then assembles each row's HED from its `HED` cell, its categorical HED, and its value templates and validates the row as a whole. If the table has an `onset` column it is a timeline and HED's temporal constructs (onset, offset, duration, delay scopes that span rows) are validated over the rows in time order; otherwise each row is validated on its own.
   - `assemble=False`: the table is never converted to a dataframe. ndx-hed reads the `HED` column and validates each distinct annotation once, and reads each categorical column to check that its values are levels of its MeaningsTable (`SIDECAR_KEY_MISSING`, a warning, as in assembled mode). Nothing that needs the other tags of a row or the other rows is checked: a tag repeated between the `HED` column and a categorical annotation, or an `Offset` without its `Onset`, is reported only with assembly.

### Where an issue points

Every issue carries the table name in `ec_table_name`; through `validate_file` it also carries the file identifier in `ec_filename`.

- A sidecar issue (a `HedValueVector` template, a MeaningsTable HED string, a definition) carries the column in `ec_sidecarColumnName` and, for categorical HED, the value in `ec_sidecarKeyName`. It has no row, because a sidecar error is not a row error.
- A row issue carries the column in `ec_column` and the row in `ec_row`, which is the table row index in both modes: the first data row is 0. (hedtools itself numbers the lines of a BIDS TSV file, header first; `validate_table` converts.)
- Where ndx-hed validates distinct values itself (the values of a `HedValueVector`, and the `HED` column with `assemble=False`), each distinct annotation is validated once and reported at the first row holding it, with the number of rows that hold it in `row_count`. The same misspelled tag on ten thousand rows is one issue.

`get_printable_issue_string` renders these as "Errors in table '<name>'", "Issues in column <name>", "Issues in row <n>", "Column '<name>':", and "Key: <value>".

### Using the table validator from nwbinspector

An inspector check receives one object. For a `DynamicTable` it finds the schema through the file and validates the table without assembly:

```python
nwbfile = table.get_ancestor("NWBFile")
hed_metadata = nwbfile.lab_meta_data.get("hed_schema") if nwbfile is not None else None
if isinstance(hed_metadata, HedLabMetaData):
    issues = HedNWBValidator(hed_metadata).validate_table(table, assemble=False)
```

Constructing a validator per table costs two attribute reads; the schema was loaded when the `HedLabMetaData` was built.

### Single-column helpers

`validate_vector` (a `HedTags` column) and `validate_value_vector` (a `HedValueVector` column) validate one column in isolation, string by string, with the row index in `ec_row`. They see no other column, no MeaningsTable, and no other row.

## Public API summary

| Function                                                    | Direction / purpose                                                                                                                  |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `extract_meanings(sidecar)`                                 | BIDS sidecar to a meanings dictionary.                                                                                               |
| `get_events_table(name, description, df, meanings)`         | BIDS dataframe plus meanings to an `EventsTable`.                                                                                    |
| `get_bids_tabular(table, hed_metadata=None)`                | Any `DynamicTable` to a BIDS `(dataframe, sidecar)` pair: `get_bids_dataframe` plus `get_json_hed_dict`. Formerly `get_bids_events`. |
| `get_bids_dataframe(table)`                                 | Any `DynamicTable` to its BIDS dataframe (`onset`, missing cells as `n/a`); reads every column.                                      |
| `get_json_hed_dict(table, hed_metadata=None)`               | Any `DynamicTable` to just its BIDS JSON sidecar dict (no dataframe, no pandas, no table data read).                                 |
| `get_levels_and_hed(meanings_table)`                        | A `MeaningsTable` to its `(Levels, HED)` sidecar dictionaries.                                                                       |
| `HedNWBValidator.validate_file(nwbfile, assemble=True)`     | Metadata check, then `validate_table` on every table in the file.                                                                    |
| `HedNWBValidator.validate_table(table, assemble=True)`      | Structural rules, sidecar, value classes, then assembled (row and temporal) validation, or with `assemble=False` cell by cell.       |
| `HedNWBValidator.validate_vector` / `validate_value_vector` | One column in isolation.                                                                                                             |

### Definitions in the exported sidecar

In NWB, HED definitions live in the `HedLabMetaData` object, which is the only place extra definitions may come from. BIDS instead carries them in the sidecar, in an entry that names no column. `get_json_hed_dict` (and `get_bids_tabular`) therefore take an optional `HedLabMetaData`; when one is supplied, its definitions are exported as

```json
{"definitions": {"HED": {"defList": "(Definition/go,(Sensory-event))"}}}
```

so the sidecar is self-contained and any `Def/` references in the table resolve from it alone. Without the metadata no such entry is written, and `Def/` references in the exported sidecar are unresolvable (`DEF_INVALID`). `HedNWBValidator` always passes its own `HedLabMetaData`, so hedtools sees the definitions exactly as a BIDS validator would; for a namespaced schema (`ts:8.5.0`) the exported `Definition` tag carries the namespace prefix.

## Relationship to BIDS

ndx-hed can represent everything BIDS can, plus arrangements BIDS does not (for example a table with no `onset`). Construction from BIDS builds an `EventsTable` (`get_events_table`); serialization to a BIDS-style tabular form works on any table (`get_bids_tabular`).
