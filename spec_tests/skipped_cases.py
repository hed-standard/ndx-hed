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

Groups: ndx-hed limits, hedtools differences, representation limits, hed-tests data bugs.
"""

SKIP_RECORDS: dict[str, str] = {
    # --- ndx-hed limits ---------------------------------------------------------------------
    # HedLabMetaData.hed_schema_version is one string, and hedtools accepts a comma-joined string
    # only when every version shares one namespace, so a mixed-namespace merge group such as
    # ['8.5.0', 'sc:testconflict_2.1.0'] cannot be represented (plan spec_tests_harness.md, F1).
    "tag-namespace_prefix-invalid-characters": "mixed-namespace schema list not representable in HedLabMetaData (F1)",
    "tag-with-namespace-has-no-schema": "mixed-namespace schema list not representable in HedLabMetaData (F1)",
    # --- hedtools differences -------------------------------------------------------------------
    # The record needs the Quantity tag and the anyUnits unit class of the HED 8.5.0 prerelease.
    # HedLabMetaData loads 8.5.0 through hedtools' cache, which holds whatever prerelease snapshot
    # was downloaded first (the one on the authoring machine has no Quantity), and the installed
    # hedtools may predate anyUnits support; the case then fails with CHARACTER_INVALID and
    # TAG_INVALID instead of UNITS_INVALID. Re-check once HED 8.5.0 is released and a hedtools
    # release bundles it with anyUnits support. hed-tests vendors a current snapshot in
    # json_test_data/test_schemas/hedxml/HED8.5.0.xml, which HedLabMetaData cannot be pointed at.
    "units-invalid-any-units": "Quantity/anyUnits need the released HED 8.5.0 and a hedtools that supports anyUnits",
}

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
    # --- hedtools differences -------------------------------------------------------------------
    # The response_time value column holds "7,3" in a row whose event_code annotation does not reference
    # {response_time}. hedtools folds a brace-referenced column into the referencing annotation and never
    # validates it on its own, so it never sees "7,3". ndx-hed checks every HedValueVector value against
    # the value class of its placeholder (rule R7, docs/source/hed_validation.md), and a comma is not
    # allowed, so it reports the value. Whether an unreferenced value must be valid is a question for
    # hed-tests; skipped until it is settled.
    ("sidecar-braces-self-reference", "combo", "passes", 1): (
        "value '7,3' in a brace-referenced column: hedtools never validates it, ndx-hed's value check does"
    ),
    # A sidecar-only case has no events table, so hedtools has nothing to resolve a {HED} column
    # reference against and reports nothing. In NWB the sidecar becomes a zero-row table (M2), whose
    # columns are known, so validate_file reports the reference to the absent HED column as the
    # SIDECAR_KEY_MISSING warning. The combo cases of this record run and pass.
    ("sidecar-refers-to-missing-tsv-hed-column", "sidecar", "passes", 1): (
        "zero-row table makes a {HED} reference resolvable, so the warning fires where hedtools has no table"
    ),
}
