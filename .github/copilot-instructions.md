# ndx-hed Copilot Instructions

This is an NWB (Neurodata Without Borders) extension for integrating HED (Hierarchical Event Descriptors) annotations into neurophysiology data files.

## Architecture Overview

**Core Extension Structure:**
- **HedLabMetaData** (`hed_lab_metadata.py`): Required schema metadata container - must be named "hed_schema", stores HED schema version and optional definitions
- **HedTags** (`hed_tags.py`): VectorData subclass for row-specific HED annotations - must be named "HED"
- **HedValueVector** (`hed_tags.py`): Template-based HED annotations with `#` placeholders for values

**Key Integration Points:**
- NWB extension spec in `spec/ndx-hed.extensions.yaml` - defines the formal data types
- Namespace loading in `__init__.py` - handles both installed and development environments
- BIDS conversion utilities in `utils/bids2nwb.py` - bidirectional BIDS ↔ NWB conversion
- Validation system in `utils/hed_nwb_validator.py` - validates HED tags against schemas

## Development Patterns

**NWB Extension Conventions:**
- All classes use `@register_class("ClassName", "ndx-hed")` decorator
- Mandatory field names: `HedLabMetaData.name` must be "hed_schema", `HedTags.name` must be "HED"
- Schema loading uses `load_namespaces()` with fallback path for git repo development

**Testing Structure:**
```bash
pytest                    # Runs all tests in src/pynwb/tests/
pytest src/pynwb/tests/test_hed_tags.py  # Specific test file
```

**Example Workflow:**
```python
# Required pattern for any HED usage
hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
nwbfile.add_lab_meta_data(hed_metadata)

# Row-specific annotations
hed_tags = HedTags(data=["Sensory-event, Visual-presentation"])
table.add_column(hed_tags)

# Template-based annotations  
hed_template = HedValueVector(hed="Sensory-event, (Duration, # s)")
```

## Critical Dependencies

- **hedtools >= 0.6.0**: Core HED validation and schema handling
- **pynwb >= 2.8.2**: Base NWB framework
- **ndx-events**: Optional integration for EventsTable support

## Common Development Tasks

**Running Examples:**
```bash
cd examples && python 01_basic_hed_classes.py
```

**Schema Validation:**
Use `HedNWBValidator` class - validates all HedTags columns in DynamicTables against the schema version specified in HedLabMetaData.

**BIDS Integration:**
- `extract_meanings()`: Converts BIDS JSON sidecars to meanings dictionary
- `get_events_table()`: Creates NWB EventsTable from BIDS events
- `get_bids_events()`: Converts EventsTable back to BIDS format

## File Organization

- `src/pynwb/ndx_hed/`: Main extension code
- `src/pynwb/tests/`: pytest-based test suite  
- `examples/`: Runnable examples (01-06) demonstrating all features
- `spec/`: YAML specifications defining the extension schema
- `requirements-dev.txt`: Pinned dev dependencies for reproducible environment

**Note:** The extension works seamlessly with both NWB core tables (trials, etc.) and ndx-events EventsTable for comprehensive event annotation.