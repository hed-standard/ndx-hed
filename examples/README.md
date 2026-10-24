# ndx-hed examples

This directory contains runnable examples demonstrating the key features of the ndx-hed extension for NWB.

## Running the examples

Each example is a standalone Python script that can be run directly:

```bash
cd examples
python 01_basic_hed_classes.py
```

To run all examples at once:

```bash
cd examples
python run_all_examples.py
```

## Example descriptions

### 01_basic_hed_classes.py

**Basic HED classes example**

- Demonstrates the three main classes: `HedLabMetaData`, `HedTags`, and `HedValueVector`
- Shows how to create HED metadata and add HED annotations to dynamic tables
- Basic usage patterns for getting started with ndx-hed
- Ends by validating the file (examples 01-04 all do, and report 0 issues)

### 02_trials_with_hed.py

**Trials example**

- Shows how to add HED annotations to the NWB trials table
- Demonstrates different types of trial annotations (stimuli, responses, rest periods)
- Common use case for behavioral experiments

### 03_events_table_integration.py

**EventsTable integration example**

- Demonstrates three ways to integrate HED with the PyNWB core `EventsTable` (NWBEP001):
  1. Direct HED column for event-specific annotations
  2. HedValueVector columns for shared annotations with value placeholders
  3. Categorical columns with HED in a `MeaningsTable`
- Shows comprehensive event annotation strategies

### 04_bids_conversion.py

**BIDS to NWB conversion example**

- Demonstrates converting BIDS events files with HED annotations to NWB format
- Shows both memory-based and file-based conversion workflows, reading the TSV with `read_bids_tsv`
- Includes sample BIDS `events.tsv` and `events.json` structures
- Exports an `EventsTable` back to a BIDS events file and sidecar with `get_bids_tabular`, reads it back, and checks that the round trip loses nothing

### 05_hed_validation.py

**HED validation example**

- Comprehensive demonstration of HED validation capabilities
- Shows validation at different levels: individual columns (`validate_vector`, `validate_value_vector`), tables (with and without row assembly), events tables, entire files
- Demonstrates custom error handlers (warnings on and off) and issue formatting with hedtools `get_printable_issue_string`
- Shows the two ndx-hed error codes for HED columns of the wrong type: `HED_COLUMN_TYPE_INVALID` and `MEANINGS_VALUE_VECTOR_INVALID`
- Includes examples of both valid and invalid HED annotations

### 06_complete_workflow.py

**Complete workflow example**

- End-to-end demonstration of the full ndx-hed workflow
- Creates an NWB file whose events table uses all three kinds of HED annotation: per-row (`HedTags`), value templates (`HedValueVector`), and categorical (a `MeaningsTable` with a HED column)
- Validates the annotations and prints each event's assembled HED, the combination validation checks
- Saves and reloads the file, checks that the `MeaningsTable` survives, and validates again

### 07_hed_definitions.py

**HED definitions example**

- Creating and using custom HED definitions in experimental contexts
- Definition validation and expansion patterns
- Advanced definition usage with value placeholders
- Integration of custom definitions with standard HED vocabulary

## Prerequisites

All examples require:

- `pynwb >= 4.2.0` (provides the core `EventsTable`, `MeaningsTable`, etc.)
- `ndx-hed` from the GitHub `main` branch (PyPI still has 0.2.0, which predates PyNWB 4)
- `pandas` (for examples 4 and 7)
- `numpy` (for example 6)

Install with:

```bash
pip install "ndx-hed @ git+https://github.com/hed-standard/ndx-hed.git" pandas numpy
```

ndx-hed from `main` brings in `pynwb>=4.2.0` and `hedtools>=1.3.0`. The first run downloads the HED 8.5.0 schema from the network; hedtools caches it in `~/.hedtools`.

## Example output

Each example includes print statements that show:

- What operations are being performed
- Success/failure status
- Validation results and issue counts
- Summary information about created objects

Run the examples to see detailed output and learn about ndx-hed functionality.

## Next steps

After running these examples:

1. Adapt the code patterns to your specific use cases
2. Refer to the main README.md for additional documentation
3. Check valid HED vocabulary using the [HED schema browser](https://www.hedtags.org/display_hed.html)
4. The [HED homepage](https://www.hedtags.org) has links to all the HED resources
5. Use the validation examples to ensure your HED annotations are correct
