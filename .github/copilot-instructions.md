# ndx-hed copilot instructions

NWB (Neurodata Without Borders) extension for integrating HED (Hierarchical Event Descriptors) annotations into neurophysiology data files. Python package targeting Python >=3.10.

When you create summaries of what you did, always put them in the `.status/` directory at the root of the repository. This directory is in `.gitignore` and is local only.

If the file `.status/local-environment.md` exists, read it before running any shell commands — it contains environment-specific setup instructions (OS, shell, virtual environment activation).

In markdown files, only capitalize the first letter of header text (sentence case).

## Line endings

All files in this repo MUST use LF (`\n`) line endings on every OS, including Windows. This is enforced by `.gitattributes` (`* text=auto eol=lf`) and local git config (`core.autocrlf=false`, `core.eol=lf`). Never introduce or commit CRLF (`\r\n`).

- **Do not write files in a way that emits CRLF.** On Windows, Python's default text mode translates `\n` to `\r\n` on write, so **never** use `open(path, "w")`, `Path.write_text(...)`, or similar text-mode writes for generating or bulk-editing files. Instead:
  - write **binary** mode with `bytes` — `open(path, "wb").write(text.encode())`, or
  - pass an explicit newline — `open(path, "w", newline="\n")`. The same applies to `sed -i` and other shell rewrites that may rewrite endings; prefer the editor's in-place edit tooling, which preserves the file's existing LF endings.
- To find CRLF files: `git ls-files --eol | grep w/crlf` (empty output means all LF).
- To fix CRLF files: rewrite each replacing `\r\n` → `\n` in binary mode, then re-run the check above and confirm it is empty.

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
- **HedTags** (`hed_tags.py`): VectorData subclass for row-specific HED annotations — must be named "HED"; at most one per DynamicTable
- **HedValueVector** (`hed_tags.py`): Template-based HED annotations with `#` placeholders for values. The annotation applies to the entire column.

**Key integration points:**

- NWB extension spec in `spec/ndx-hed.extensions.yaml` — defines the formal data types
- Namespace loading in `__init__.py` — handles both installed and development environments
- BIDS conversion utilities in `utils/bids2nwb.py` — bidirectional BIDS ↔ NWB conversion
- Validation system in `utils/hed_nwb_validator.py` — validates HED tags against schemas

## Development patterns

**NWB extension conventions:**

- All classes use `@register_class("ClassName", "ndx-hed")` decorator
- Mandatory names: `HedLabMetaData.name` is "hed_schema", `HedTags.name` is "HED" (≤1 per DynamicTable). `HedValueVector` may have any name.
- Schema loading uses `load_namespaces()` with fallback path for git repo development

**Example workflow:**

```python
from datetime import datetime, timezone
from pynwb import NWBFile
from pynwb.core import DynamicTable, VectorData
from ndx_hed import HedLabMetaData, HedTags, HedValueVector

# Required first step for any HED usage: create the file and add the HED schema metadata
nwbfile = NWBFile(
    session_description="HED example",
    identifier="example_001",
    session_start_time=datetime.now(timezone.utc),
)
nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version="8.4.0"))

# Build a DynamicTable with a row-specific HedTags column (must be named "HED") and a
# template-based HedValueVector column (one HED template with a "#" placeholder per value)
table = DynamicTable(
    name="events",
    description="Events with HED annotations",
    columns=[
        VectorData(name="event_time", description="Event times", data=[1.0, 2.0]),
        HedTags(data=["Sensory-event, Visual-presentation", "Agent-action"]),
        HedValueVector(
            name="duration",
            description="Event durations",
            data=[0.5, 1.0],
            hed="(Duration, # s)",
        ),
    ],
)
nwbfile.add_acquisition(table)
```

## Critical dependencies

- **hedtools >= 1.2.0**: Core HED validation and schema handling
- **pynwb >= 4.0.0**: Base NWB framework; provides the core EventsTable/MeaningsTable (NWBEP001)
- **hdmf >= 6.1.0**: Required by pynwb; provides MeaningsTable and DynamicTable.get_meanings_for_column

## Common development tasks

**Running examples:**

```bash
cd examples && python 01_basic_hed_classes.py
```

**Schema validation:** Use `HedNWBValidator` class — validates all HedTags columns in DynamicTables against the schema version specified in HedLabMetaData.

**BIDS integration:**

- `extract_meanings()`: Converts BIDS JSON sidecars to meanings dictionary
- `get_events_table()`: Creates NWB EventsTable from BIDS events
- `get_bids_tabular()`: Converts a DynamicTable to BIDS format (DataFrame + sidecar)

## File organization

- `src/pynwb/ndx_hed/`: Main extension code
- `src/pynwb/tests/`: pytest-based test suite
- `examples/`: Runnable examples (01–07) demonstrating all features
- `spec/`: YAML specifications defining the extension schema
- `pyproject.toml`: Build config, dependencies, and ruff lint settings
- `pytest.ini`: Test configuration
- `constraints/`: Pinned and minimum dependency constraint files

The extension works with both NWB core tables (trials, etc.) and the PyNWB core EventsTable (NWBEP001) for comprehensive event annotation.
