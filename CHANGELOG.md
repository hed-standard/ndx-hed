# Changelog for ndx-hed

## Release 1.0.0

Migration to PyNWB 4.0.0. NWBEP001 (`EventsTable`, `MeaningsTable`, `TimestampVectorData`, `DurationVectorData`, etc.) has been merged into PyNWB core, so ndx-hed no longer depends on the standalone `ndx-events` extension.

### Breaking changes

- **Dependencies**: now requires `pynwb>=4.0.0` and `hdmf>=6.1.0`; the `ndx-events` dependency has been removed. `EventsTable`, `TimestampVectorData`, and `DurationVectorData` are now imported from `pynwb.event`; `MeaningsTable` from `hdmf.common`. Use the standard `pynwb.NWBFile` (the `NdxEventsNWBFile` type no longer exists).
- **No `CategoricalVectorData`** (the categorical column type formerly provided by the `ndx-events` extension): PyNWB 4.0.0 did not introduce an equivalent. Any `DynamicTable` column (a plain `VectorData`) can now be annotated by a `MeaningsTable`.
- **Reversed column-meanings relationship**: a `MeaningsTable` is now bound to the column it annotates via a required `target` argument (`MeaningsTable(target=column, ...)`), and its name is auto-derived as `"{column_name}_meanings"`. Meanings are attached to a table with `table.add_meanings_table(...)` and retrieved with `table.get_meanings_for_column(col_name)`. A `MeaningsTable` can no longer be constructed standalone.
- **HED column rules clarified/enforced**: a `HedTags` column must be named `"HED"`, and therefore there is at most one `HedTags` column per `DynamicTable`. A `HedTags` column inside a `MeaningsTable` provides categorical (per-value) HED; in any other `DynamicTable` it provides per-row HED. A `HedValueVector` (a value template, which never had a fixed name) must not appear in a `MeaningsTable`. Two rules are new: a column named `HED` must be a `HedTags` (a `VectorData` or `HedValueVector` named `HED` is reported as `HED_COLUMN_TYPE_INVALID`), and the values of a `HedValueVector` must satisfy the value class of its `#` tag (a `#` with no value class is `textClass`; for `Def/Name/#` the class comes from the placeholder inside the definition). The `HedValueVector`-in-`MeaningsTable` rule is now reported as the issue `MEANINGS_VALUE_VECTOR_INVALID` instead of raising `ValueError`. All rules are in `docs/source/hed_validation.md`. The `HedValueVector` schema doc was corrected (it previously and incorrectly stated "Always has the name HED").
- **`HedNWBValidator.validate_table` rewritten as the table validator, and `validate_events` removed.** `validate_table(table, error_handler=None, assemble=True)` runs, in order: the structural rules (an issue stops the table); nothing for a table without HED, which is not read; the BIDS sidecar dict through `get_json_hed_dict`, with the `HedLabMetaData` definitions in it; hedtools `Sidecar.validate` (any error stops the table); the value-class check of every `HedValueVector` (any error stops); then, with `assemble=True`, the whole table as a BIDS dataframe through hedtools `TabularInput.validate` (per cell, per row, and temporal when an `onset` column is present). With `assemble=False`, for nwbinspector, the table is never converted to a dataframe: the `HED` column is validated cell by cell and categorical values are checked against their levels, and nothing that needs the other tags of a row or the other rows. `validate_file(nwbfile, error_handler=None, assemble=True)` now does only the metadata check and calls `validate_table` per table, so the two agree table for table. A `MeaningsTable` passed to `validate_table` raises `ValueError`; its HED is validated with the table it annotates. `validate_events(events)` is `validate_table(events)`.
- **Row numbers and collapsed issues**: a row issue's `ec_row` is the table row index (first data row 0) in every path; previously the assembled path reported hedtools' BIDS line number, header first. Where ndx-hed validates distinct values itself (`HedValueVector` values, and the `HED` column with `assemble=False`) each distinct annotation is validated once and reported at its first row with the number of rows holding it in `row_count`. Issues from a table no longer carry the table name in `ec_filename`; through `validate_file` that key is the file identifier and the table is in `ec_table_name`.

### Changes

- `bids2nwb`: `extract_meanings()` now returns the raw sidecar column-info dicts for categorical columns (the `MeaningsTable` is built later, once the target column exists); `get_categorical_meanings()` now takes the target `VectorData` column instead of a column name; `get_events_table()` builds categorical columns as plain `VectorData` and attaches a `MeaningsTable` to each. **`get_bids_events()` was renamed to `get_bids_tabular()`** and generalized to convert **any** `DynamicTable` (not just an `EventsTable`) to a BIDS `(dataframe, sidecar)` pair; it looks up meanings via the table. The sidecar half of that conversion is now the separate public function **`get_json_hed_dict(table, hed_metadata=None)`**, which builds the BIDS JSON sidecar dict straight from the table's columns without a dataframe or pandas, together with **`get_levels_and_hed(meanings_table)`**, which returns a `MeaningsTable`'s `(Levels, HED)` dictionaries. `get_bids_tabular()` now delegates to `get_json_hed_dict()`, so both produce identical sidecars. Both accept an optional `HedLabMetaData` -- the only place extra HED definitions may come from in NWB -- and export its definitions under the BIDS `"definitions"` sidecar key, making the exported sidecar self-contained for `Def/` references. Passing anything other than a `HedLabMetaData` raises `ValueError`.
- `HedNWBValidator.validate_file()` performs **assembled** (BIDS-style) validation of every `DynamicTable` except `MeaningsTable`, through `validate_table` (see the breaking-changes entry): each table's sidecar is validated first, then the table is converted to a dataframe and validated with hedtools `TabularInput`, which combines a row's direct/categorical/value HED into one annotation; temporal when the table has an `onset` column. A `MeaningsTable` is not validated on its own; its categorical HED is validated as part of the table whose column it annotates. `validate_vector()` and `validate_value_vector()` remain as single-column helpers.
- `get_bids_tabular()` is now `get_bids_dataframe(table)` plus `get_json_hed_dict(table, hed_metadata)`, both public. `get_bids_dataframe()` writes missing cells (NaN, None, the empty string) as `n/a`, as a BIDS TSV would, so a missing value in a `HedValueVector` column no longer produces a false `VALUE_INVALID` (`Delay/nan s`) on the assembled path. `HedLabMetaData.definitions` (the exported definitions string) now carries the schema namespace prefix on the `Definition` tag for a namespaced schema and no longer writes `None` for a definition without contents.
- The ndx-hed error codes `HED_COLUMN_TYPE_INVALID` and `MEANINGS_VALUE_VECTOR_INVALID` are registered with hedtools' `hed_error` in the new module `ndx_hed.utils.hed_nwb_errors`, so the issues have the same shape as hedtools' own.
- `HedLabMetaData` is unchanged (still named "hed_schema").
- `validate_vector()` and `validate_value_vector()` no longer revalidate an annotation that has already been validated in the same column and found to have no issues. The issues returned are unchanged, including the reporting of every row of a repeated annotation that does have issues, but a column of many rows drawn from a few event types is now validated in roughly the time of its distinct annotations rather than its rows.
- `validate_vector()` and `validate_value_vector()` (and `get_levels_and_hed()`) read a column in a single slice instead of one element at a time. The issues returned are unchanged; validating a 20,000-row `HedTags` column read from an HDF5 file drops from roughly 0.5 s to roughly 0.01 s.
- Every issue records its table in the hedtools `TABLE_NAME` error context (`ec_table_name`); `get_printable_issue_string` prints it as "Errors in table '<name>'". `validate_file()` uses `FILE_NAME` (`ec_filename`) for the NWB file identifier.
- New `spec_tests/` directory runs the hed-tests validation suite (the sidecar, event, and combo cases of `validation_tests.json`; hed-tests is a git submodule) through `HedNWBValidator.validate_file`, converting each case to NWB objects with the library's own BIDS converters. Cases the NWB representation cannot hold, or that need a hedtools feature not yet available, are skipped with a stated reason in `spec_tests/skipped_cases.py`. Run with `python -m pytest spec_tests`; see `spec_tests/README.md`. The stale, unreferenced copy of `validation_tests.json` under `src/pynwb/tests_json/` was removed.
- `HedNWBValidator.validate_table()` (and so `validate_file()`) stops validating a table after any error in its sidecar-level HED (a `HedValueVector` template, a MeaningsTable HED string, or a definition), not only after a structural sidecar error. Such an error would be repeated on every row that uses it and would make the assembled row annotations unreliable. The sidecar issues name the column and the categorical value (`ec_sidecarColumnName`, `ec_sidecarKeyName`) and have no row. Warnings alone do not stop validation.
- `spec_tests/skipped_cases.py`: two named skips added for cases the new rules change: `sidecar-invalid-key-at-wrong-level sidecar[fails 2]` (a top-level `HED` key becomes a `VectorData` named `HED`, reported as `HED_COLUMN_TYPE_INVALID` before hedtools sees it) and `sidecar-braces-self-reference combo[passes 1]` (a value `7,3` in a brace-referenced column that hedtools never validates on its own).

## Release 0.2.0 October 18, 2025

Major rewrite and expansion of the ndx-hed extension with three core classes and comprehensive tooling. Web pages with API docs hosted on Github.

### New features

#### Core classes

- **HedLabMetaData**: Required metadata container for storing HED schema version and optional custom definitions

  - Must be added to `NWBFile` before using any HED annotations
  - Supports both standard and library schemas
  - Includes `DefinitionDict` for custom HED definitions
  - Methods: `get_hed_schema()`, `get_definition_dict()`, `add_definitions()`, `extract_definitions()`

- **HedTags**: VectorData subclass for row-specific HED annotations in DynamicTables

  - Must be named "HED" (enforced by constructor)
  - Stores one HED string per row
  - Works with any NWB DynamicTable (trials, units, epochs, etc.)

- **HedValueVector**: VectorData subclass for column-wide HED templates with value placeholders

  - Stores numerical/categorical data with associated HED annotation template
  - Uses `#` placeholder for values (e.g., "Duration/# s")
  - HED annotation applies to entire column

#### Validation system

- **HedNWBValidator**: Comprehensive validation class for HED annotations in NWB files
  - `validate_file()`: Validates entire `NWBFile`
  - `validate_dynamic_table()`: Validates specific DynamicTable
  - `validate_hed_tags()`: Validates individual HedTags column
  - `validate_hed_value_vector()`: Validates HedValueVector columns
  - Supports both in-memory and file-based validation
  - **Full definition support**: All validation methods now support external HED definitions from `HedLabMetaData`
  - Validates definition references (e.g., `Def/Go-stimulus`) across all HED annotation types

#### BIDS integration

- **Bidirectional BIDS-NWB conversion utilities** in `utils/bids2nwb.py`:
  - `extract_meanings()`: Converts BIDS JSON sidecars to meanings dictionary
  - `get_categorical_meanings()`: Creates MeaningsTable from BIDS categorical columns
  - `get_events_table()`: Converts BIDS events.tsv + sidecar to NWB EventsTable
  - `get_bids_events()`: Converts EventsTable back to BIDS format (DataFrame + sidecar)
  - `extract_definitions()`: Extracts HED definitions from BIDS sidecars

#### ndx-events integration

- Full support for EventsTable, MeaningsTable, CategoricalVectorData
- Three integration patterns:
  1. Direct HED column for event-specific annotations
  2. HedValueVector columns for shared annotations with values
  3. Categorical columns with HED in MeaningsTable

### Examples

Seven comprehensive runnable examples demonstrating all features:

- `01_basic_hed_classes.py`: Introduction to HedLabMetaData, HedTags, and HedValueVector
- `02_trials_with_hed.py`: Adding HED annotations to NWB trials table
- `03_events_table_integration.py`: Three patterns for EventsTable integration
- `04_bids_conversion.py`: Bidirectional BIDS-NWB conversion workflows
- `05_hed_validation.py`: Comprehensive validation examples
- `06_complete_workflow.py`: End-to-end workflow with file I/O
- `07_hed_definitions.py`: Custom HED definitions and expansion

### Dependencies

- Updated to `hedtools>=0.7.1` (released to PyPI)
- `pynwb>=2.8.2`
- `hdmf>=3.14.1`
- Optional: `ndx-events>=0.4.0` for EventsTable support

### Testing

- 78 comprehensive test cases for HedNWBValidator
- 116+ total test cases across all modules
- Full coverage of all core classes and utilities
- File I/O roundtrip testing
- Validation testing with valid and invalid HED
- BIDS conversion roundtrip testing
- Definition handling and persistence testing
- Definition reference validation across all validator methods

### Breaking changes from 0.1.0

- **HedTags constructor changes**: Removed `hed_version` parameter (now uses HedLabMetaData)
- **New requirement**: HedLabMetaData must be added to `NWBFile` before using HED annotations
- **Name enforcement**: HedTags must be named "HED", HedLabMetaData must be named "hed_schema"

### Documentation

- Updated user guide for 0.2.0 architecture
- Comprehensive example suite with runnable code
- Updated README with Quick Start guide

## Release 0.1.0 July 25, 2024

- Implements a `HedTags` class that extends NWB `VectorData`.
- Validates tags in the constructor and as they are added.
- The `HedTags` class can be used alone or added to any `DynamicTable`.
- The initial release only supports string HED version specifications, not tuples or lists.
