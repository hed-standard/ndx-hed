"""
Check that the hed-tests submodule is present before running the spec tests.

Run from the repository root: ``python spec_tests/check_setup.py``.
"""

import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
VALIDATION_TESTS = os.path.join(HERE, "hed-tests", "json_test_data", "validation_tests.json")


def main() -> int:
    if os.path.isfile(VALIDATION_TESTS):
        print(f"OK: found {VALIDATION_TESTS}")
        return 0
    print(f"MISSING: {VALIDATION_TESTS}")
    print("Initialize the submodule from the repository root:")
    print("    git submodule update --init spec_tests/hed-tests")
    return 1


if __name__ == "__main__":
    sys.exit(main())
