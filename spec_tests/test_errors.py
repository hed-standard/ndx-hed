"""
Run the hed-tests validation suite through ndx-hed as a unittest.

The work is done by ``run_cases`` (see its docstring for what is converted and how). This module
runs every sidecar, event, and combo case with the defaults and fails once per kind if any case
failed. It has no options on purpose: to run one record, the skip list, or write a report, use the
command line in ``run_cases``::

    python -m spec_tests.run_cases --help

Run with ``python -m pytest spec_tests -v`` from the repository root (``-s`` shows the summary
even when everything passes).
"""

import unittest

from .run_cases import MISSING_MESSAGE, load_records, print_summary, run_kind


class TestHedTestsValidation(unittest.TestCase):
    """Run each kind of hed-tests case through validate_file and compare with the expected codes."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_records()

    def test_sidecar_cases(self):
        self._run_kind("sidecar")

    def test_event_cases(self):
        self._run_kind("event")

    def test_combo_cases(self):
        self._run_kind("combo")

    def _run_kind(self, kind):
        if self.records is None:
            self.skipTest(MISSING_MESSAGE)
        result = run_kind(self.records, kind)
        print_summary(result)
        self.assertEqual(result.failed, 0, f"{result.failed} {kind} case(s) failed; see the report above")


if __name__ == "__main__":
    unittest.main()
