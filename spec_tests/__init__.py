"""
Specification tests for ndx-hed.

This package runs the hed-tests validation suite (the test suite of record for HED validators,
vendored as the git submodule ``spec_tests/hed-tests``) through ndx-hed: each sidecar, event, and
combo case is converted to NWB objects and validated with ``HedNWBValidator.validate_file``.
It is run separately from the unit tests: ``python -m pytest spec_tests``.
"""
