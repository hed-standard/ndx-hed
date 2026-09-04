# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`ndx-hed` is an NWB (Neurodata Without Borders) extension that adds HED (Hierarchical Event Descriptors) annotations to any NWB `DynamicTable`. Python >= 3.10. The current line (1.0.0) targets PyNWB 4.x, where `EventsTable`/`MeaningsTable` are part of NWB core (NWBEP001) — the old `ndx-events` dependency is gone.

## Environment setup

The project is developed and CI-tested on Linux, macOS, and Windows (Python 3.10–3.14). Install the dev extras against the known-good pinned snapshot:

```bash
python -m venv .venv
source .venv/bin/activate          # POSIX
# .venv\Scripts\Activate.ps1       # Windows PowerShell
# .venv\Scripts\activate.bat       # Windows cmd.exe
pip install -e ".[dev]" -c constraints/pinned.txt
```

`constraints/minimum.txt` holds the declared minimums (keep in sync with `pyproject.toml` dependencies); CI runs `minimum`, `pinned`, and `upgraded` variants across all three OSes (`.github/workflows/run_all_tests.yml`).

Command blocks below use POSIX shell syntax; translate for PowerShell as needed (chain with `;` — `&&` works in PowerShell 7+ but not 5.1). If `.status/local-environment.md` exists (gitignored, so present only on machines that created it), read it before running shell commands — it records that machine's OS, shell, and venv specifics and takes precedence over the generic guidance here.

## Commands

```bash
pytest                                                      # full suite (pytest.ini: testpaths=src/pynwb/tests, -v)
pytest src/pynwb/tests/test_hed_nwb_validator.py            # one file
pytest src/pynwb/tests/test_hed_tags.py::TestHedTagsConstructor::test_constructor   # one test
pytest --cov=src/pynwb/ndx_hed --cov-report=term            # with coverage

ruff check .                # lint (config in pyproject.toml, line-length 120)
ruff format --check .       # formatting check
ruff format .               # auto-format
typos .                     # spell check
```

`pytest` and `ruff check .` must pass before committing.

Examples must be run from inside `examples/` — `run_all_examples.py` and the individual scripts resolve paths relative to the working directory:

```bash
cd examples
python run_all_examples.py       # all of 01-07
python 01_basic_hed_classes.py   # just one
```

Docs build from `docs/` (`make html` on POSIX, `make.bat html` on Windows without GNU make); output lands in `docs/_build/html`.

## Repository conventions

- **LF line endings everywhere**, on every OS (enforced by `.gitattributes`: `* text=auto eol=lf`; contributors on Windows should also set `core.autocrlf=false` and `core.eol=lf`). This only needs care on Windows, where Python's text mode translates `\n` to `\r\n` on write: do not use `open(path, "w")`, `Path.write_text()`, or `sed -i` for generating or bulk-editing files — write binary mode with `bytes`, or pass `newline="\n"`. Prefer in-place edit tooling, which preserves existing endings. Check with `git ls-files --eol | grep w/crlf` (POSIX) or `git ls-files --eol | Select-String w/crlf` (PowerShell); empty output means clean.
- Put work summaries in `.status/` (gitignored, so it is local scratch and starts empty in a fresh clone). Where it does exist it may hold useful design notes (`RulesForHEDinNWB.md`, `HedTableValidationModes.md`, `NWBMigrationNotes.md`); the committed counterpart is `docs/source/hed_validation.md`.
- Markdown headers use sentence case (capitalize only the first word).
- `spec/*.yaml` is **generated** — edit `src/spec/create_extension_spec.py` and run `python src/spec/create_extension_spec.py`, then reinstall so the namespace reloads.

## Architecture

### Three extension types

All are registered with `@register_class("<Name>", "ndx-hed")` and declared in `src/spec/create_extension_spec.py`.

| Class                            | File                  | Constraint                                                                                                                                                                  |
| -------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HedLabMetaData` (`LabMetaData`) | `hed_lab_metadata.py` | name forced to `"hed_schema"`; loads the `HedSchema` and a `DefinitionDict` in the constructor, so a constructed instance is guaranteed valid. Required before any HED use. |
| `HedTags` (`VectorData`)         | `hed_tags.py`         | name must be `"HED"` (constructor raises otherwise), hence at most one per table                                                                                            |
| `HedValueVector` (`VectorData`)  | `hed_tags.py`         | any name; carries a `hed` template that must contain exactly one `#`                                                                                                        |

`src/pynwb/ndx_hed/__init__.py` calls `load_namespaces()` on the installed `ndx_hed/spec/` path, falling back to the repo's top-level `spec/` when running from a git checkout — keep both paths working.

### HED column rules (R1–R5)

Documented in `docs/source/hed_validation.md`; these drive most of the code:

1. R1 — a `HedTags` column must be named `HED` (constructor).
2. R2 — at most one `HedTags` column per `DynamicTable` (follows from R1).
3. R3 — a `HedTags` column *inside a `MeaningsTable`* is categorical (per-value) HED for the column that MeaningsTable targets.
4. R4 — a `HedTags` column in any other `DynamicTable` is per-row HED.
5. R5 — a `HedValueVector` must not appear in a `MeaningsTable` (`validate_file` raises `ValueError`).

So three distinct HED shapes coexist: per-row (`HedTags`), value template (`HedValueVector`, `#` substituted per row), and categorical (plain `VectorData` + `MeaningsTable` holding a `HED` column).

### Validation pipeline

`utils/hed_nwb_validator.py` is where the design lives. `HedNWBValidator.validate_file` does **assembled**, BIDS-style validation rather than tag-by-tag checks, because HED meaning depends on the rest of the row and, for time-anchored tables, on other rows:

1. Convert each table to `(dataframe, sidecar)` with `get_bids_tabular` (`utils/bids2nwb.py`).
2. `Sidecar.validate()` first — only this step performs brace-structure / `{column}`-reference checks. Structural failures (`STRUCTURAL_SIDECAR_CODES`) short-circuit, because continuing produces misleading downstream errors.
3. `TabularInput.validate()` on the assembled table — merges each row's per-row + categorical + value HED into one annotation, carries file/column/row context, and validates **temporally (timeline)** when an `onset` column is present, non-temporally otherwise. Mode selection is automatic; `get_bids_tabular` renames a `TimestampVectorData` column to `onset` precisely so an `EventsTable` is treated as a timeline.
4. Sidecar issues for categorical levels that never occur in the data are added back (`_unused_categorical_level_issues`), since `TabularInput` only sees values present in the data.

`MeaningsTable`s are skipped in the file walk (their HED is validated as part of the table they annotate) and only checked against R5. `validate_table`, `validate_vector`, and `validate_value_vector` are per-column helpers that do *not* assemble rows or validate temporally.

### BIDS ↔ NWB (`utils/bids2nwb.py`)

- `extract_meanings(sidecar_data)` → `{"categorical": {...raw sidecar column-info...}, "value": {col: hed_string}}`. Categorical entries stay raw because a PyNWB 4 `MeaningsTable` requires the target `VectorData` object, which does not exist yet.
- `get_events_table(name, description, df, meanings)` builds the `EventsTable` (`onset`→`TimestampVectorData` named `timestamp`, `duration`→`DurationVectorData`, value columns→`HedValueVector`, `HED`→`HedTags`, categorical→plain `VectorData`), then attaches a `MeaningsTable` per categorical column via `add_meanings_table`.
- `get_bids_tabular(table)` is the inverse for **any** `DynamicTable` (renamed from `get_bids_events` in 1.0.0). It emits nothing for the `HED` column (`HED` is a reserved sidecar key and the column is self-describing) and reads categorical levels through `DynamicTable.get_meanings_for_column`.

Validation reuses this converter, so a change to `get_bids_tabular` changes validation behavior.

## Tests

`src/pynwb/tests/` — unittest style via `pynwb.testing.TestCase`, with `mock_NWBFile` and roundtrip tests through `NWBHDF5IO`. Test fixtures (BIDS `.tsv` / sidecar `.json`) are in `src/pynwb/tests/data/`. Tests load real HED schemas from the network on first use.

## Docs

Sphinx sources in `docs/source/`. `docs/source/_format_auto_docs/` is regenerated from `spec/*.yaml` by `make apidoc` — never hand-edit. `docs/source/hed_validation.md` is the narrative spec for the rules and validation modes; keep it in sync with validator changes. Published at <https://www.hedtags.org/ndx-hed>.
