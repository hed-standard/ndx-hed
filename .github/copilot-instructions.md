# ndx-hed copilot instructions

NWB (Neurodata Without Borders) extension for integrating HED (Hierarchical Event Descriptors) annotations into neurophysiology data files. Python package targeting Python >=3.10.

When you create summaries of what you did, always put them in the `.status/` directory at the root of the repository. This directory is in `.gitignore` and is local only.

If the file `.status/local-environment.md` exists, read it before running any shell commands — it contains environment-specific setup instructions (OS, shell, virtual environment activation).

In markdown files, only capitalize the first letter of header text (sentence case).

## Environment setup

```bash
python -m venv .venv
# Activate the virtual environment (see .status/local-environment.md for OS-specific command)
pip install -e ".[dev]"
```

## Testing

```bash
pytest                                              # All tests (configured via pytest.ini)
pytest src/pynwb/tests/test_hed_tags.py             # Single test file
pytest --cov=src/pynwb/ndx_hed --cov-report=term   # With coverage
```

Test configuration is in `pytest.ini` (`testpaths = src/pynwb/tests`).

## Linting

```bash
ruff check .            # Check for style errors
ruff format --check .   # Check formatting
ruff format .           # Auto-format
```

Ruff configuration is in `pyproject.toml`. Always ensure `pytest` and `ruff check .` pass before committing.

## CI workflows

All workflows are in `.github/workflows/`:
- `run_all_tests.yml` — runs pytest on Python 3.10–3.14 across Linux/Windows/macOS on every push
- `ruff.yml` — runs ruff linter and format check on PRs/pushes to main
- `typos.yaml` — spell checking
- `run_coverage.yml` — coverage reporting
- `docs.yml` — builds Sphinx documentation

## Architecture overview

**Core extension structure:**
- **HedLabMetaData** (`hed_lab_metadata.py`): Required schema metadata container — must be named "hed_schema", stores HED schema version and optional definitions
- **HedTags** (`hed_tags.py`): VectorData subclass for row-specific HED annotations — must be named "HED"
- **HedValueVector** (`hed_tags.py`): Template-based HED annotations with `#` placeholders for values. The annotation applies to the entire column.

**Key integration points:**
- NWB extension spec in `spec/ndx-hed.extensions.yaml` — defines the formal data types
- Namespace loading in `__init__.py` — handles both installed and development environments
- BIDS conversion utilities in `utils/bids2nwb.py` — bidirectional BIDS ↔ NWB conversion
- Validation system in `utils/hed_nwb_validator.py` — validates HED tags against schemas

## Development patterns

**NWB extension conventions:**
- All classes use `@register_class("ClassName", "ndx-hed")` decorator
- Mandatory field names: `HedLabMetaData.name` must be "hed_schema", `HedTags.name` must be "HED"
- Schema loading uses `load_namespaces()` with fallback path for git repo development

**Example workflow:**
```python
# Required pattern for any HED usage
hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
nwbfile.add_lab_meta_data(hed_metadata)

# Row-specific annotations
hed_tags = HedTags(data=["Sensory-event, Visual-presentation"])
table.add_column(hed_tags)

# Template-based annotations
hed_template = HedValueVector(hed="Sensory-event, (Duration, # s)")
```

## Critical dependencies

- **hedtools >= 0.7.1**: Core HED validation and schema handling
- **pynwb >= 2.8.2**: Base NWB framework
- **hdmf >= 3.14.1**: Required by pynwb
- **ndx-events >= 0.4.0**: EventsTable support

## Common development tasks

**Running examples:**
```bash
cd examples && python 01_basic_hed_classes.py
```

**Schema validation:**
Use `HedNWBValidator` class — validates all HedTags columns in DynamicTables against the schema version specified in HedLabMetaData.

**BIDS integration:**
- `extract_meanings()`: Converts BIDS JSON sidecars to meanings dictionary
- `get_events_table()`: Creates NWB EventsTable from BIDS events
- `get_bids_events()`: Converts EventsTable back to BIDS format

## File organization

- `src/pynwb/ndx_hed/`: Main extension code
- `src/pynwb/tests/`: pytest-based test suite
- `examples/`: Runnable examples (01–07) demonstrating all features
- `spec/`: YAML specifications defining the extension schema
- `pyproject.toml`: Build config, dependencies, and ruff lint settings
- `pytest.ini`: Test configuration
- `constraints/`: Pinned and minimum dependency constraint files

The extension works with both NWB core tables (trials, etc.) and ndx-events EventsTable for comprehensive event annotation.