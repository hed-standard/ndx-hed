"""
Cases of the hed-tests validation suite that ndx-hed does not run yet, each with its reason.

Two granularities:

- ``SKIP_RECORDS`` maps a record name (the ``name`` field in validation_tests.json) to a reason and
  skips every sidecar, event, and combo case of that record.
- ``SKIP_CASES`` maps ``(record name, kind, result, index)`` to a reason and skips one case. ``kind``
  is ``"sidecar"``, ``"event"``, or ``"combo"``; ``result`` is ``"passes"`` or ``"fails"``; ``index``
  is the 1-based position in that list, the number the harness prints as ``sidecar[3]``.

Rule-based skips (a ragged row, a sidecar entry for a column the events lack) are computed by the
harness and are not listed here. A schema that HedLabMetaData cannot load is a failure, not a skip.

Run ``python -m spec_tests.run_cases --include-skipped`` to run the listed cases anyway, for example
to re-check the list after a fix. Every entry needs a reason; when a reason no longer holds, remove
the entry.

Groups, when an entry needs one: ndx-hed limits, hedtools differences, representation limits, hed-tests
data bugs. Test-only schema libraries are not a reason to skip: the harness resolves them against the
vendored hed-tests folder (run_cases.test_schema_cache).
"""

# No whole record is skipped today. The last entries were the two mixed-namespace schema records (lifted
# 2026-10 when HedLabMetaData's JSON-array form reached the harness) and units-invalid-any-units (lifted
# when hedtools gained anyUnits and the harness started resolving 8.5.0 against the vendored snapshot).
SKIP_RECORDS: dict[str, str] = {}

SKIP_CASES: dict[tuple[str, str, str, int], str] = {
    # --- representation limits ------------------------------------------------------------------
    # SIDECAR_INVALID: the HED key at the wrong nesting level, or 'HED' used as a column name in the
    # sidecar. These are malformed sidecar JSON. NWB has no sidecar JSON; its column metadata is
    # typed (MeaningsTable, HedValueVector), so the malformed shape cannot be built at all. The
    # record's passes cases are well-formed and run.
    ("sidecar-invalid-key-at-wrong-level", "sidecar", "fails", 1): "malformed sidecar JSON has no NWB equivalent",
    ("sidecar-invalid-key-at-wrong-level", "combo", "fails", 1): "malformed sidecar JSON has no NWB equivalent",
    ("sidecar-invalid-key-at-wrong-level", "combo", "fails", 2): "malformed sidecar JSON has no NWB equivalent",
    # The sidecar's top-level key is 'HED', so the harness builds a VectorData named HED (M2). ndx-hed
    # reports that as HED_COLUMN_TYPE_INVALID (rule R6, docs/source/hed_validation.md) before hedtools
    # sees the table, where the expected code is SIDECAR_INVALID. Same malformed shape as the entries above.
    ("sidecar-invalid-key-at-wrong-level", "sidecar", "fails", 2): (
        "a top-level HED key becomes a VectorData named HED, which ndx-hed reports as HED_COLUMN_TYPE_INVALID"
    ),
    # A sidecar-only case has no events table, so hedtools has nothing to resolve a {HED} column
    # reference against and reports nothing. In NWB the sidecar becomes a zero-row table (M2), whose
    # columns are known, so validate_file reports the reference to the absent HED column as the
    # SIDECAR_KEY_MISSING warning. The combo cases of this record run and pass.
    ("sidecar-refers-to-missing-tsv-hed-column", "sidecar", "passes", 1): (
        "zero-row table makes a {HED} reference resolvable, so the warning fires where hedtools has no table"
    ),
}
