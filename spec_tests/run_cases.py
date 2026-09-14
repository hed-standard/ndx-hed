"""
Run the hed-tests validation suite through ndx-hed.

Every sidecar, event, and combo case of ``spec_tests/hed-tests/json_test_data/validation_tests.json``
is converted to NWB objects (see ``nwb_case_builder``) and validated with
``HedNWBValidator.validate_file``. String cases are not run: hedtools covers them and NWB has no
string-only object. Modeled on hed-python's ``spec_tests/test_errors.py``; the expected-result rule
is the same.

``test_errors.py`` runs every kind with the defaults. For debugging, this module is also a
command line::

    python -m spec_tests.run_cases --help
    python -m spec_tests.run_cases --kind combo --only units-invalid-any-units
    python -m spec_tests.run_cases --list-skipped
    python -m spec_tests.run_cases --include-skipped --report .status/scratch/spec_report.json

Run from the repository root.
"""

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass, field

from hed.errors import ErrorHandler, SchemaWarnings, get_printable_issue_string

from ndx_hed.utils.hed_nwb_validator import HedNWBValidator

from .nwb_case_builder import (
    SCHEMA_LOAD_PREFIX,
    absent_hed_columns,
    build_combo_table,
    build_events_table,
    build_metadata,
    build_nwbfile,
    build_sidecar_table,
    is_ragged,
    split_definition_entries,
)
from .skipped_cases import SKIP_CASES, SKIP_RECORDS

HERE = os.path.dirname(os.path.realpath(__file__))
VALIDATION_TESTS = os.path.join(HERE, "hed-tests", "json_test_data", "validation_tests.json")
MISSING_MESSAGE = f"{VALIDATION_TESTS} not found; run: git submodule update --init spec_tests/hed-tests"

KIND_KEYS = {"sidecar": "sidecar_tests", "event": "event_tests", "combo": "combo_tests"}
KINDS = tuple(KIND_KEYS)

# Outcomes of one case.
PASSED = "passed"
CONSTRUCTION_REJECTED = "construction_rejected"  # NWB refused the case; counts as passed for a fails case
FAILED = "failed"
SKIPPED = "skipped"


@dataclass
class KindResult:
    """Everything one run of a kind produced: counts, skip reasons, failures, and every outcome."""

    kind: str
    counts: dict = field(default_factory=lambda: {PASSED: 0, CONSTRUCTION_REJECTED: 0, FAILED: 0, SKIPPED: 0})
    skip_reasons: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)  # (label, record, case, detail)
    outcomes: list = field(default_factory=list)  # one dict per case, for the optional report

    @property
    def failed(self):
        return len(self.failures)


def load_records(path=VALIDATION_TESTS):
    """Return the records of validation_tests.json, or None when the submodule is not checked out."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


# --------------------------------------------------------------------------------------------
# Driver


def run_kind(records, kind, *, only=None, include_skipped=False):
    """Run every case of one kind and return a KindResult.

    :param records: the list loaded by load_records.
    :param kind: "sidecar", "event", or "combo".
    :param only: record names or error codes to run; empty or None means every record. Exact match.
    :param include_skipped: also run the cases listed in skipped_cases.py (rule-based skips still apply).
    """
    if kind not in KIND_KEYS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")
    only = set(only or ())
    result = KindResult(kind)
    for record in records:
        if only and record["name"] not in only and record["error_code"] not in only:
            continue
        tests = record["tests"].get(KIND_KEYS[kind]) or {}
        for expected in ("passes", "fails"):
            for index, case in enumerate(tests.get(expected) or [], 1):
                outcome, detail = run_case(record, kind, expected, index, case, include_skipped=include_skipped)
                result.counts[outcome] += 1
                label = f"{record['name']} {kind}[{expected} {index}]"
                result.outcomes.append({
                    "record": record["name"],
                    "error_code": record["error_code"],
                    "kind": kind,
                    "result": expected,
                    "index": index,
                    "outcome": outcome,
                    "detail": detail,
                })
                if outcome == SKIPPED:
                    result.skip_reasons[detail] = result.skip_reasons.get(detail, 0) + 1
                elif outcome == FAILED:
                    result.failures.append((label, record, case, detail))
    return result


def run_case(record, kind, expected, index, case, *, include_skipped=False):
    """Return (outcome, detail) for one case. detail is a skip reason, a failure reason, or the codes."""
    skip = named_skip(record["name"], kind, expected, index, include_skipped)
    if skip:
        return SKIPPED, skip

    # Rule-based skips and the M5 split of definitions entries.
    extra_definitions = []
    sidecar = None
    rows = None
    if kind == "sidecar":
        sidecar, extra_definitions = split_definition_entries(case, None)
    elif kind == "event":
        rows = case
    else:
        rows = case["events"]
        sidecar, extra_definitions = split_definition_entries(case["sidecar"], rows[0])
        absent = absent_hed_columns(sidecar, rows[0])
        if absent:
            return SKIPPED, "sidecar entry for a column the events lack; NWB attaches HED only to a column (M6)"
    if rows is not None and is_ragged(rows):
        return SKIPPED, "ragged events row (hed-tests data bug)"

    # M1: metadata. A schema that cannot be loaded is a harness failure, never a skip: the schemas a case
    # needs are known in advance (a version hedtools lacks is a named skip in skipped_cases.py), so a
    # load failure here means a network or cache problem, and skipping would leave an offline run green.
    # Any other ValueError is a bad definition, a construction rejection.
    try:
        metadata = build_metadata(record["schema"], record.get("definitions"), extra_definitions)
    except ValueError as e:
        if str(e).startswith(SCHEMA_LOAD_PREFIX):
            return FAILED, f"schema {record['schema']} could not be loaded (network, cache, or version):\n{e}"
        return construction_outcome(expected, f"HedLabMetaData: {e}")

    # M2-M4: the table.
    try:
        if kind == "sidecar":
            table = build_sidecar_table(sidecar)
        elif kind == "event":
            table = build_events_table(rows)
        else:
            table = build_combo_table(sidecar, rows)
    except ValueError as e:
        return construction_outcome(expected, f"{type(e).__name__}: {e}")
    except Exception:  # noqa: BLE001 - one broken case must not stop the run
        return FAILED, "harness error while building the table:\n" + traceback.format_exc()

    # Validate.
    try:
        nwbfile = build_nwbfile(metadata, table)
        error_handler = ErrorHandler(check_for_warnings=bool(record.get("warning", False)))
        issues = HedNWBValidator(metadata).validate_file(nwbfile, error_handler)
    except Exception:  # noqa: BLE001
        return FAILED, "validate_file raised:\n" + traceback.format_exc()
    issues = [issue for issue in issues if issue["code"] != SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED]
    return compare(record, expected, issues)


# --------------------------------------------------------------------------------------------
# Result rule (from hed-python report_result) plus the construction rule


def compare(record, expected, issues):
    codes = [issue["code"] for issue in issues]
    allowed = [record["error_code"]] + list(record.get("alt_codes") or [])
    if expected == "fails":
        if not issues:
            return FAILED, f"should fail with one of {allowed} but produced no issues"
        if any(code in allowed for code in codes):
            return PASSED, codes
        return FAILED, f"wrong code: expected one of {allowed}, got {codes}\n{get_printable_issue_string(issues)}"
    if issues:
        return FAILED, f"should pass but got {codes}\n{get_printable_issue_string(issues)}"
    return PASSED, codes


def construction_outcome(expected, message):
    if expected == "fails":
        return CONSTRUCTION_REJECTED, message
    return FAILED, f"should pass but NWB rejected it at construction: {message}"


def named_skip(name, kind, expected, index, include_skipped):
    if include_skipped:
        return None
    return SKIP_RECORDS.get(name) or SKIP_CASES.get((name, kind, expected, index))


# --------------------------------------------------------------------------------------------
# Report


def print_summary(result):
    counts = result.counts
    total = sum(counts.values())
    print("\n" + "=" * 80)
    print(f"hed-tests {result.kind} cases through ndx-hed validate_file")
    print("=" * 80)
    print(f"Total:                  {total}")
    print(f"Passed:                 {counts[PASSED]}")
    print(f"Rejected at construction (counted as expected failures): {counts[CONSTRUCTION_REJECTED]}")
    print(f"Failed:                 {counts[FAILED]}")
    print(f"Skipped:                {counts[SKIPPED]}")
    for reason, count in sorted(result.skip_reasons.items(), key=lambda item: -item[1]):
        print(f"    {count:4d}  {reason}")
    if result.failures:
        print("-" * 80)
        print(f"{result.failed} failure(s):")
        for label, record, case, detail in result.failures:
            print(f"\n[FAIL] {label}  (expects {record['error_code']}, schema {record['schema']})")
            print(f"  {record['description']}")
            print(f"  case: {json.dumps(case)[:400]}")
            print(f"  {detail}")
    print("=" * 80)


def skip_source(outcome):
    """Say where a skipped case's reason came from: SKIP_RECORDS, SKIP_CASES, or a harness rule."""
    if SKIP_RECORDS.get(outcome["record"]) == outcome["detail"]:
        return "SKIP_RECORDS"
    key = (outcome["record"], outcome["kind"], outcome["result"], outcome["index"])
    if SKIP_CASES.get(key) == outcome["detail"]:
        return "SKIP_CASES"
    return "rule"


def print_skipped(result):
    """List every skipped case of one kind, grouped by reason, one line per case."""
    skipped = [outcome for outcome in result.outcomes if outcome["outcome"] == SKIPPED]
    print(f"Skipped {result.kind} cases ({len(skipped)}):")
    if not skipped:
        return
    by_reason = {}
    for outcome in skipped:
        by_reason.setdefault(outcome["detail"], []).append(outcome)
    for reason, group in sorted(by_reason.items(), key=lambda item: (-len(item[1]), item[0])):
        print(f"  {reason}  [{skip_source(group[0])}]")
        for outcome in group:
            print(f"      {outcome['record']} {outcome['kind']}[{outcome['result']} {outcome['index']}]")


def write_report(path, outcomes):
    """Write every case outcome to a JSON file (LF line endings on every OS), creating its directory."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fp:
        json.dump(outcomes, fp, indent=1)


# --------------------------------------------------------------------------------------------
# Command line


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m spec_tests.run_cases",
        description="Run the hed-tests validation suite through ndx-hed and print a summary per kind.",
    )
    parser.add_argument(
        "--kind", choices=KINDS + ("all",), default="all", help="which kind of case to run (default: all)"
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        metavar="NAME_OR_CODE",
        help="run only records whose name or error code equals one of these values (exact match)",
    )
    parser.add_argument(
        "--include-skipped",
        action="store_true",
        help="also run the cases listed in skipped_cases.py (rule-based skips still apply)",
    )
    parser.add_argument(
        "--list-skipped",
        action="store_true",
        help="after each summary, list every skipped case grouped by reason, with where the reason came from",
    )
    parser.add_argument("--report", metavar="PATH", help="also write every case outcome to this JSON file")
    args = parser.parse_args(argv)

    records = load_records()
    if records is None:
        print(MISSING_MESSAGE, file=sys.stderr)
        return 2
    known = {record["name"] for record in records} | {record["error_code"] for record in records}
    unknown = sorted(set(args.only) - known)
    if unknown:
        print(f"--only: no record has this name or error code: {', '.join(unknown)}", file=sys.stderr)
        return 2

    kinds = KINDS if args.kind == "all" else (args.kind,)
    outcomes = []
    failed = 0
    for kind in kinds:
        result = run_kind(records, kind, only=args.only, include_skipped=args.include_skipped)
        print_summary(result)
        if args.list_skipped:
            print_skipped(result)
        outcomes.extend(result.outcomes)
        failed += result.failed
    if args.report:
        write_report(args.report, outcomes)
        print(f"Wrote {len(outcomes)} outcome(s) to {args.report}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
