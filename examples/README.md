# NDX-HED examples

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

### 02_trials_with_hed.py
**Trials example**
- Shows how to add HED annotations to the NWB trials table
- Demonstrates different types of trial annotations (stimuli, responses, rest periods)
- Common use case for behavioral experiments

### 03_events_table_integration.py
**EventsTable integration example**
- Demonstrates three ways to integrate HED with ndx-events `EventsTable`:
  1. Direct HED column for event-specific annotations
  2. HedValueVector columns for shared annotations with value placeholders
  3. Categorical columns with HED in `MeaningsTable`
- Shows comprehensive event annotation strategies

### 04_bids_conversion.py
**BIDS to NWB conversion example**
- Demonstrates converting BIDS events files with HED annotations to NWB format
- Shows both memory-based and file-based conversion workflows
- Includes sample BIDS `events.tsv` and `events.json` structures

### 05_hed_validation.py
**HED validation example**
- Comprehensive demonstration of HED validation capabilities
- Shows validation at different levels: individual columns, tables, events tables, entire files
- Demonstrates custom error handlers and issue categorization
- Includes examples of both valid and invalid HED annotations

### 06_complete_workflow.py
**Complete workflow example**
- End-to-end demonstration of the full ndx-hed workflow
- Creates comprehensive NWB file with all types of HED annotations
- Validates annotations and handles issues
- Tests file save/reload consistency
- Real-world usage patterns and best practices

### 07_hed_definitions.py
**HED definitions example**
- Creating and using custom HED definitions in experimental contexts
- Definition validation and expansion patterns
- Advanced definition usage with value placeholders
- Integration of custom definitions with standard HED vocabulary

## Prerequisites

All examples require:
- `pynwb`
- `ndx-hed`
- `ndx-events` (for examples 3-8)
- `pandas` (for example 4)
- `numpy` (for example 8)

Install with:
```bash
pip install pynwb ndx-hed ndx-events pandas
```

## Example Output

Each example includes print statements that show:
- What operations are being performed
- Success/failure status
- Validation results and issue counts
- Summary information about created objects

Run the examples to see detailed output and learn about ndx-hed functionality.

## Next Steps

After running these examples:
1. Adapt the code patterns to your specific use cases
2. Refer to the main README.md for additional documentation
3. Check valid HED vocabulary using the [HED schema browser](https://www.hedtags.org/display_hed.html)
3. The [HED homepage](https://www.hedtags.org) has links to all the HED resources
4. Use the validation examples to ensure your HED annotations are correct
