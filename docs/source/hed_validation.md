# HED annotation and validation in ndx-hed

This document describes how HED (Hierarchical Event Descriptors) annotations are represented in NWB tables, the rules ndx-hed follows, and how the validator works. It reflects the 1.0.0 design (PyNWB 4.0.0, where EventsTable, MeaningsTable, and related types are part of NWB core).

## Representing HED in a table

There are three ways a column contributes HED to a table, mirroring the two BIDS sidecar forms:

- Per-row HED: a `HedTags` column stores one HED string per row.
- Value HED: a `HedValueVector` column stores one HED template containing a single `#` placeholder; the placeholder is replaced by each row's value to produce that row's annotation.
- Categorical HED: a plain column of category labels is annotated by a `MeaningsTable`, which maps each distinct value to a meaning and (optionally) a HED string held in a `HedTags` column named `HED` inside the MeaningsTable.

`MeaningsTable` is a core hdmf type. ndx-hed does not define it; ndx-hed carries categorical HED by adding a `HedTags` column to it.

## HED column rules

The following five rules govern how HED columns may appear in an NWB table.

- Rule R1: A `HedTags` column must be named `HED`.
- Rule R2: A `DynamicTable` has at most one `HedTags` column.
- Rule R3: A `HedTags` column inside a `MeaningsTable` provides categorical (per-value) HED for the column that the MeaningsTable annotates.
- Rule R4: A `HedTags` column in any other `DynamicTable` provides per-row HED for that table.
- Rule R5: A `HedValueVector` must not appear in a `MeaningsTable`.

### How each rule is enforced

| Rule | How it is enforced                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------ |
| R1   | `HedTags.__init__` raises `ValueError` if the name is not `HED` (which is also the default).                 |
| R2   | Follows from R1: column names within a table are unique, so two `HED` columns cannot coexist.                |
| R3   | The MeaningsTable's `HED` column is consumed as categorical HED when assembling the annotated table.         |
| R4   | The table's `HED` column is assembled as its per-row HED.                                                    |
| R5   | `HedNWBValidator.validate_file` raises `ValueError` if a `MeaningsTable` contains a `HedValueVector` column. |

Notes:

- `HedValueVector` may have any column name and is identified by its neurodata type, not by name.
- The `HedValueVector` schema documentation previously stated "Always has the name HED"; that was incorrect and has been corrected.

## How validation works

HED is not validated only tag-by-tag. Its meaning depends on the other HED in the same row, and for time-anchored tables on the other rows. There are two validation modes.

### Two modes: timeline and non-timeline

- Non-timeline: rows are not anchored to time. Each row's complete HED annotation is assembled from all of that row's columns and validated independently of the other rows.
- Timeline: rows are anchored to time (there is an `onset` column). In addition to per-row assembly, HED's temporal constructs (for example onset, offset, duration, and delay scopes that span rows) are validated over the events in time order.

The mode is determined automatically. A time-anchored table (for example an `EventsTable`, whose `timestamp` column is exported as `onset`) is validated as a timeline; a table with no `onset` column is validated as non-timeline.

### Assembled validation

`HedNWBValidator.validate_file` validates every `DynamicTable` except `MeaningsTable` using assembled validation, in two steps:

1. The table is converted to a BIDS-style dataframe and JSON sidecar with `get_bids_tabular`.
2. The sidecar (column metadata: value templates and categorical Levels/HED) is validated first with `Sidecar.validate`, then the assembled table is validated with `TabularInput.validate`. `TabularInput.validate` combines each row's per-row HED, categorical HED, and value-template HED into a single annotation before validating, and applies temporal validation when an `onset` column is present.

Both steps are required. `TabularInput.validate` does NOT re-run the sidecar's brace-structure and column-reference checks (self, nested, invalid, or malformed `{column}` references); those are only performed by `Sidecar.validate`. If the sidecar were validated only through the assembled table, those structural problems would be missed and would instead surface as misleading downstream errors (for example a stray `{` reported as `CHARACTER_INVALID`). Therefore the sidecar is validated explicitly first; if it has any error, the sidecar issues are returned and the assembled-table step is skipped. Stopping is deliberate: a sidecar-level error (a bad value template or a bad categorical HED string) would be repeated on every row that uses it, and the row annotations assembled from it cannot be trusted, so continuing would only add noise. Sidecar issues carry the table name (`ec_table_name`), the column (`ec_sidecarColumnName`), and for categorical HED the value (`ec_sidecarKeyName`); they have no row, because a sidecar error is not a row error. Warnings alone do not stop validation.

A `MeaningsTable` is not validated on its own. Its categorical HED is validated as part of the table whose column it annotates. A `MeaningsTable` is only checked against rule R5.

### Per-column helpers

`validate_table`, `validate_vector`, and `validate_value_vector` remain available for validating a single table or a single column in isolation (per-column checks). These do not perform row assembly or temporal validation; use `validate_file` (or `validate_events` for a single EventsTable) for full assembled validation.

Every issue returned by `validate_table` and `validate_file` carries the table name in `ec_table_name`. The rest of the location depends on the kind of issue:

- A row issue (an error in a `HedTags` cell, or in a `HedValueVector` value after substitution) carries the column name in `ec_column` and the row in `ec_row`. `validate_table` reports the 0-based row index; the assembled path in `validate_file` reports the 1-based row of the BIDS-style table, counting the header.
- A sidecar issue (an error in a `HedValueVector` template or in a MeaningsTable HED string) carries the column in `ec_sidecarColumnName` and, for categorical HED, the value in `ec_sidecarKeyName`. It has no row. In `validate_table` a template error likewise has the column in `ec_column` and no row.

`get_printable_issue_string` renders these as "Errors in table '<name>'", "Issues in column <name>", "Issues in row <n>", "Column '<name>':", and "Key: <value>". Each column is read in a single slice, so validating a file-backed column costs one read rather than one read per row.

## Public API summary

| Function                                                                   | Direction / purpose                                                                   |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `extract_meanings(sidecar)`                                                | BIDS sidecar to a meanings dictionary.                                                |
| `get_events_table(name, description, df, meanings)`                        | BIDS dataframe plus meanings to an `EventsTable`.                                     |
| `get_bids_tabular(table, hed_metadata=None)`                               | Any `DynamicTable` to a BIDS `(dataframe, sidecar)` pair. Formerly `get_bids_events`. |
| `get_json_hed_dict(table, hed_metadata=None)`                              | Any `DynamicTable` to just its BIDS JSON sidecar dict (no dataframe, no pandas).      |
| `get_levels_and_hed(meanings_table)`                                       | A `MeaningsTable` to its `(Levels, HED)` sidecar dictionaries.                        |
| `HedNWBValidator.validate_file(nwbfile)`                                   | Assembled validation of every table in a file.                                        |
| `HedNWBValidator.validate_events(events)`                                  | Assembled validation of a single `EventsTable`.                                       |
| `HedNWBValidator.validate_table / validate_vector / validate_value_vector` | Per-column validation of a table or column.                                           |

### Definitions in the exported sidecar

In NWB, HED definitions live in the `HedLabMetaData` object, which is the only place extra definitions may come from. BIDS instead carries them in the sidecar, in an entry that names no column. `get_json_hed_dict` (and `get_bids_tabular`) therefore take an optional `HedLabMetaData`; when one is supplied, its definitions are exported as

```json
{"definitions": {"HED": {"defList": "(Definition/go,(Sensory-event))"}}}
```

so the sidecar is self-contained and any `Def/` references in the table resolve from it alone. Without the metadata no such entry is written, and `Def/` references in the exported sidecar are unresolvable (`DEF_INVALID`) unless the definitions are supplied separately - which is what `HedNWBValidator` does internally, passing the `DefinitionDict` from its own `HedLabMetaData` as hedtools' `extra_def_dicts`.

## Relationship to BIDS

ndx-hed can represent everything BIDS can, plus arrangements BIDS does not (for example a table with no `onset`). Construction from BIDS builds an `EventsTable` (`get_events_table`); serialization to a BIDS-style tabular form works on any table (`get_bids_tabular`).
