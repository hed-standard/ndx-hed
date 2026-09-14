# Spec tests

The `spec_tests/` directory runs the [hed-tests](https://github.com/hed-standard/hed-tests) validation suite, the test suite of record for HED validators, through ndx-hed. Each sidecar, event, and combo case in `hed-tests/json_test_data/validation_tests.json` is converted to NWB objects and validated with `HedNWBValidator.validate_file`; the codes it reports are compared with the codes the case expects. The layout follows hed-python's `spec_tests/`.

Not run here: `string_tests` (hedtools covers them, and NWB has no string-only object), the schema tests (`schema_tests.json`), and the schema-loading tests.

## Setup

hed-tests is a git submodule at `spec_tests/hed-tests`. After cloning ndx-hed:

```bash
git submodule update --init spec_tests/hed-tests
python spec_tests/check_setup.py
```

The pinned commit is what `git submodule status` prints. To move the pin to the current hed-tests `main`:

```bash
git submodule update --remote spec_tests/hed-tests
```

then run the spec tests, update `skipped_cases.py` if new cases need it, and commit the new gitlink together with those changes.

## Running

From the repository root, with the development environment installed:

```bash
python -m pytest spec_tests -v
```

The spec tests are not part of the default `python -m pytest` run (`pytest.ini` limits `testpaths` to the unit tests). CI runs them in `.github/workflows/spec_tests.yml`. Each of the three test methods (`test_sidecar_cases`, `test_event_cases`, `test_combo_cases`) prints a summary with the counts of passed, rejected-at-construction, failed, and skipped cases, lists every failure with the case data and the issues found, and fails once if any case failed. Run with `-s` to see the summary even when everything passes.

The pytest run has no options on purpose: a test that can be narrowed silently is a test whose green result means nothing. To run one record, run the skip list, or keep every outcome, use the command line in `run_cases.py`, which does the work for `test_errors.py`:

```bash
python -m spec_tests.run_cases --help
python -m spec_tests.run_cases --kind combo --only units-invalid-any-units
python -m spec_tests.run_cases --only UNITS_INVALID --include-skipped
python -m spec_tests.run_cases --list-skipped
python -m spec_tests.run_cases --report .status/scratch/spec_report.json
```

`--only` takes record names or error codes (exact match) and refuses a value that matches no record; `--include-skipped` runs the cases listed in `skipped_cases.py` too (rule-based skips still apply); `--list-skipped` prints every skipped case under its reason, marked `SKIP_RECORDS`, `SKIP_CASES`, or `rule` by where the reason came from; `--report` writes every case outcome to a JSON file. The exit code is 0 when every case passed, 1 when any failed, 2 when the submodule is missing or `--only` names nothing.

## How a JSON case becomes NWB

The code is in `nwb_case_builder.py`, which uses the library's own converters (`extract_meanings`, `get_categorical_meanings`, `get_events_table`) wherever one exists, so the spec tests exercise the converters as well as the validator. The rules:

| Rule                   | JSON                                                                                               | NWB                                                                                                                                                                                                                                                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M1 record              | `schema`, `definitions`                                                                            | one `HedLabMetaData` per case; a list-valued `schema` is joined with commas, the definitions list with `", "`                                                                                                                                                                                                         |
| M2 sidecar case        | sidecar dict                                                                                       | a zero-row `DynamicTable`: a dict-`HED` (or `Levels`) entry becomes an empty `VectorData` with a `MeaningsTable`, a string-`HED` entry an empty `HedValueVector`, a description-only entry an empty `VectorData`. hedtools validates every level and template whether or not rows use them, so zero rows lose nothing |
| M3 event case          | header row plus data rows                                                                          | `get_events_table` when the header has `onset` (an `EventsTable`, validated as a timeline); otherwise a plain `DynamicTable` with the same column rules (`HED` -> `HedTags`, others `VectorData`)                                                                                                                     |
| M4 combo case          | sidecar plus events                                                                                | `extract_meanings(sidecar)` then M3, which attaches the `MeaningsTable`s and builds the `HedValueVector`s: exactly the library's BIDS import                                                                                                                                                                          |
| M5 definitions entry   | a sidecar entry whose column the events lack and whose `HED` dict values all contain `Definition/` | folded into the `HedLabMetaData` definitions, which is where ndx-hed keeps definitions. Malformed definitions are then rejected when the `HedLabMetaData` is constructed                                                                                                                                              |
| M6 other absent column | a HED-bearing sidecar entry whose column the events lack, not M5                                   | skipped with a reason: NWB attaches HED only to a column that exists                                                                                                                                                                                                                                                  |
| M7 warnings            | record `warning: true`                                                                             | `ErrorHandler(check_for_warnings=True)`                                                                                                                                                                                                                                                                               |

Rejected at construction: `HedValueVector` refuses a template without exactly one `#`, and `HedLabMetaData` refuses an invalid definition. The harness records such a `ValueError` as an outcome of its own. For a `fails` case it counts as the expected failure (the representation rejected what the validator would have flagged) and is reported separately so the number stays visible; for a `passes` case it is a failure. Note that the rejection may be for a different reason than the case's expected code, since a constructor does not report HED error codes.

## Expected-result rule

The same as hed-python's `report_result`: `SCHEMA_PRERELEASE_VERSION_USED` issues are dropped; a `fails` case passes when any remaining issue code is in `[error_code] + alt_codes`; a `passes` case passes when no issue remains. Row numbers are not compared.

## Skips

Two layers, both counted by reason in the summary:

- Rule-based, computed from the case by the harness: a ragged events row; a HED-bearing sidecar entry for a column the events lack (M6); a `schema` that `HedLabMetaData` cannot load.
- Named, in `skipped_cases.py`: `SKIP_RECORDS` for whole records and `SKIP_CASES` for single cases, keyed by `(record name, kind, result, index)` with a 1-based index within the `passes` or `fails` list. Every entry has a reason, grouped by ndx-hed limits, hedtools differences, representation limits, and hed-tests data bugs. When a reason no longer holds, remove the entry.

## Files

- `hed-tests/` - the submodule.
- `check_setup.py` - reports whether the submodule is present.
- `nwb_case_builder.py` - the M1-M7 conversion, as pure functions.
- `test_case_builder.py` - unit tests for the conversion, one hand-written case per rule; they need no submodule.
- `skipped_cases.py` - the named skip list.
- `run_cases.py` - the harness: runs the cases, applies the expected-result rule, prints the summary; also the command line above.
- `test_errors.py` - the unittest wrapper around `run_cases.py`, with no options.
