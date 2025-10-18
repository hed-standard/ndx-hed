# Changelog for ndx-hed

## Release 0.2.0 October 18, 2025

Major rewrite and expansion of the ndx-hed extension with three core classes and comprehensive tooling. Web pages with API docs hosted on Github.

### New Features

#### Core Classes
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

#### Validation System
- **HedNWBValidator**: Comprehensive validation class for HED annotations in NWB files
  - `validate_file()`: Validates entire `NWBFile`
  - `validate_dynamic_table()`: Validates specific DynamicTable
  - `validate_hed_tags()`: Validates individual HedTags column
  - `validate_hed_value_vector()`: Validates HedValueVector columns
  - Supports both in-memory and file-based validation
  - **Full definition support**: All validation methods now support external HED definitions from `HedLabMetaData`
  - Validates definition references (e.g., `Def/Go-stimulus`) across all HED annotation types

#### BIDS Integration
- **Bidirectional BIDS ↔ NWB conversion utilities** in `utils/bids2nwb.py`:
  - `extract_meanings()`: Converts BIDS JSON sidecars to meanings dictionary
  - `get_categorical_meanings()`: Creates MeaningsTable from BIDS categorical columns
  - `get_events_table()`: Converts BIDS events.tsv + sidecar to NWB EventsTable
  - `get_bids_events()`: Converts EventsTable back to BIDS format (DataFrame + sidecar)
  - `extract_definitions()`: Extracts HED definitions from BIDS sidecars

#### ndx-events Integration
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
- `04_bids_conversion.py`: Bidirectional BIDS ↔ NWB conversion workflows
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

### Breaking Changes from 0.1.0
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