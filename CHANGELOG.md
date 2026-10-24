# Changelog for ndx-hed

## Release 0.3.0 October 24, 2026

The first ndx-hed release for PyNWB 4, which closes issue #194. NWBEP001 (`EventsTable`, `MeaningsTable`, `TimestampVectorData`, `DurationVectorData`) is now part of PyNWB and HDMF core, so ndx-hed no longer depends on the standalone `ndx-events` extension. Validation now runs through hedtools' staged tabular validator, so an NWB table is validated the way hedtools validates a BIDS events file. The HED rules for NWB tables are documented in `docs/source/hed_validation.md`.

### Breaking changes

#### Dependencies and core types

- Requires `pynwb>=4.2.0`, `hdmf>=6.2.0`, and `hedtools>=1.3.0`; the `ndx-events` dependency is removed.
- `EventsTable`, `TimestampVectorData`, and `DurationVectorData` are imported from `pynwb.event`, and `MeaningsTable` from `hdmf.common`. Use the standard `pynwb.NWBFile`; `NdxEventsNWBFile` no longer exists.
- There is no `CategoricalVectorData`. A categorical column is a plain `VectorData` annotated by a `MeaningsTable`.
- A `MeaningsTable` is bound to the column it annotates: `MeaningsTable(target=column, ...)`, named `"{column_name}_meanings"`, attached with `table.add_meanings_table(...)` and read back with `table.get_meanings_for_column(col_name)`. It can no longer be built on its own.

#### Validation (`HedNWBValidator`)

- `validate_events()` is removed; call `validate_table(events)`.
- `validate_table(table, error_handler=None, assemble=True)` now validates the whole table. In 0.2.0 it checked each `HedTags` and `HedValueVector` column on its own. It now applies the structural rules, validates the table's HED as a BIDS sidecar (value templates, categorical HED from each `MeaningsTable`, and the `HedLabMetaData` definitions), checks the column values, and with `assemble=True` (the default) validates each row's combined per-row, categorical, and value HED, temporally when the table has an `onset` column. Each stage stops on an error; warnings alone do not stop it. Sidecar-stage issues name the column and categorical value (`ec_sidecarColumnName`, `ec_sidecarKeyName`) and have no row. With `assemble=False` (for tools such as nwbinspector) no dataframe is built, and each distinct `HED` string is checked on its own; the checks that need the whole row or other rows (required tags, temporal) do not run. Passing a `MeaningsTable` raises `ValueError`; its HED is validated with the table it annotates.
- `validate_file(nwbfile, error_handler=None, assemble=True)` checks the `HedLabMetaData` and then calls `validate_table` for every `DynamicTable` except a `MeaningsTable`. It compares schemas by `get_formatted_version()`, which also works for a schema group or a merged library schema.
- Issues are reported per distinct value. A `HED` string, `HedValueVector` value, or categorical value with a problem is reported once, at the first row holding it, with the number of such rows in `row_count` (`ROW_COUNT_KEY`). That includes `validate_vector()`, which in 0.2.0 reported every row.
- `ec_row` is the table row index (first data row 0) in every path; it used to be hedtools' BIDS line number in the assembled path. Every issue names its table in `ec_table_name`. Through `validate_file`, `ec_filename` holds the NWB file identifier; it no longer holds the table name.
- A `HedValueVector` placed in a `MeaningsTable` is now reported as the issue `MEANINGS_VALUE_VECTOR_INVALID` instead of raising `ValueError`.

#### BIDS conversion (`ndx_hed.utils.bids2nwb`)

- `get_bids_events(events_table)` is renamed `get_bids_tabular(table, hed_metadata=None)`, and it accepts any `DynamicTable`.
- `get_categorical_meanings()` takes the target `VectorData` column instead of a column name.
- `extract_meanings()` returns the raw sidecar column-info dict for each categorical column instead of a built table. The `MeaningsTable` is built by `get_events_table()` once the target column exists.
- `get_events_table()` builds categorical columns as plain `VectorData`, each with a `MeaningsTable`. It turns the BIDS `n/a` spellings in `onset` and `duration` into NaN and raises on any other non-numeric value instead of passing it through.

### Changes

#### HED rules

- New rule: a column named `HED` must be a `HedTags`. A `VectorData` or `HedValueVector` named `HED` is reported as `HED_COLUMN_TYPE_INVALID`.
- New rule: the values of a `HedValueVector` must satisfy the value class of its `#` tag. A `#` with no value class is `textClass`, and for `Def/Name/#` the class comes from the placeholder in the definition. Each distinct value is checked as the `#` tag with the value in place, so a value that breaks HED syntax (`a)`, `a#b`) is rejected.
- The HED specification 4.0.0 rules for tabular files apply, through hedtools: a column name repeated, padded, or blank is `TABULAR_INVALID` (a `TimestampVectorData` named `timestamp` counts as `onset`); a padded value in a categorical or `HedValueVector` column is `TABULAR_INVALID`; a padded `MeaningsTable` value that carries HED is `SIDECAR_INVALID`.
- `{column}` references in `HedValueVector` templates are checked by the sidecar stage; a per-row `HED` column may not contain them.
- The new module `ndx_hed.utils.hed_nwb_errors` registers the ndx-hed codes `HED_COLUMN_TYPE_INVALID` and `MEANINGS_VALUE_VECTOR_INVALID` with hedtools, so their issues have the same shape as hedtools' own.

#### Validation helpers

- `validate_vector()` and `validate_value_vector()` remain as single-column helpers. Each validates every distinct value once, so a long column drawn from a few annotations takes roughly the time of its distinct values. Each also reads the column in one slice: a 20,000-row `HedTags` column read from HDF5 validates in about 0.01 s instead of 0.5 s. Their issues carry `ec_column`.
- `validate_value_vector()` validates the template with its `{column}` references removed (they are resolved only by `validate_table`), then the values; a template whose parentheses do not balance is reported.
- A `HedValueVector` whose dtype settles its value class (for example a numeric column under a `numericClass` tag) is not read.
- Missing values (`None`, `""`, `n/a`, and any NaN, including numpy float32 and float16) are skipped. An integer too large for a float is a valid value, not an `OverflowError`.

#### BIDS conversion

- `get_bids_tabular()` is now two public halves: `get_bids_dataframe(table)` and `get_json_hed_dict(table, hed_metadata=None)`. `get_json_hed_dict` builds the sidecar from the table's columns without reading the data or using pandas. `get_levels_and_hed(meanings_table)` returns a `MeaningsTable`'s `Levels` and `HED` dictionaries.
- Given a `HedLabMetaData`, `get_json_hed_dict()` and `get_bids_tabular()` export its definitions under the sidecar's `"definitions"` key (`DEFINITIONS_KEY`), so the sidecar resolves its `Def/` references. Anything else raises `ValueError`.
- `get_bids_dataframe()` writes missing cells (NaN, None, `""`) as `n/a`, as a BIDS TSV does, so a missing `HedValueVector` value is no longer a `VALUE_INVALID` (`Delay/nan s`).
- `get_bids_dataframe()`, `get_bids_tabular()`, and `get_events_table()` raise `ValueError` for a repeated column name.
- `get_categorical_meanings()` keeps a value listed only under `HED`, which used to be dropped with its annotation. A value listed only under `Levels` gets an empty HED cell; an explicit `n/a` stays.
- New `read_bids_tsv(path)` reads a BIDS TSV file the way hedtools does: every cell as text, a double quote an ordinary character, only an empty cell and `n/a` missing, and the header names exactly as written. `pd.read_csv` defaults would rename a repeated `HED` to `HED.1` and read `NA` and `null` as missing.

#### HedLabMetaData

- `hed_schema_version` accepts one version string (`"8.4.0"`), a comma-joined string of versions in one namespace (`"8.4.0,score_2.1.0"`), or a list or tuple of versions (`["8.4.0", "sc:score_2.1.0"]`). A list is stored as the JSON array string hedtools reads and writes, so the NWB attribute stays one text value.
- The exported definitions string carries the schema namespace prefix on the `Definition` tag for a namespaced schema, and no longer writes `None` for a definition without contents.

#### Format, packaging, and documentation

- The NWB namespace version is 0.3.0. The data types are unchanged from 0.2.0 apart from their doc strings (the `HedValueVector` doc used to say, wrongly, that it is always named `HED`). Files written from the development `main` branch before this release cache namespace version 1.0.0; they open and validate with 0.3.0, with an hdmf warning that the cached namespace is ignored.
- `setup.py`, `requirements-dev.txt`, and `requirements-min.txt` are removed. Development installs use the `test`, `dev`, and `docs` extras in `pyproject.toml`, with `constraints/minimum.txt` and `constraints/pinned.txt`.
- The examples are rewritten for PyNWB 4. Each validates what it builds; they show the three HED shapes together in one events table with its assembled row HED (`06_complete_workflow.py`), the NWB to BIDS round trip (`04_bids_conversion.py`), and the ndx-hed error codes (`05_hed_validation.py`). `run_all_examples.py` now runs each example's `main()`; before, it only imported them.
- New documentation page `docs/source/hed_validation.md` gives the HED rules for NWB tables and the validation modes. The release notes page includes this file instead of keeping a copy.
- New `spec_tests/` directory runs the hed-tests validation suite through `validate_file` (`python -m pytest spec_tests`; see `spec_tests/README.md`).

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
