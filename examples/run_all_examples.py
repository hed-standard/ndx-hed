#!/usr/bin/env python3
"""
Run All NDX-HED Examples
========================

This script runs all the examples to verify they work correctly.
Use this to test the examples or as a demonstration of all ndx-hed features.

"""

import sys
import importlib.util
import traceback


def run_example(example_name, description):
    """Run a single example and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {example_name}")
    print(f"Description: {description}")
    print(f"{'='*60}")

    try:
        # Import and run the example
        spec = importlib.util.spec_from_file_location("example", f"{example_name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        print(f"\n✓ {example_name} completed successfully!")
        return True

    except Exception as e:
        print(f"\n✗ {example_name} failed with error:")
        print(f"Error: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        return False


def main():
    """Run all examples"""
    print("NDX-HED Examples Test Suite")
    print("Running all examples to verify functionality...")

    examples = [
        ("01_basic_hed_classes.py", "Basic HED classes demonstration"),
        ("02_trials_with_hed.py", "Adding HED to trials table"),
        ("03_events_table_integration.py", "EventsTable integration with HED"),
        ("04_bids_conversion.py", "BIDS to NWB conversion"),
        ("05_hed_validation.py", "HED validation examples"),
        ("06_complete_workflow.py", "Complete end-to-end workflow"),
        ("07_hed_definitions.py", "Custom HED definitions usage"),
        ("08_advanced_integration.py", "Advanced real-world integration"),
    ]

    results = []

    for example_name, description in examples:
        success = run_example(example_name, description)
        results.append((example_name, success))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    successful = sum(1 for _, success in results if success)
    total = len(results)

    print(f"Examples run: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")

    print("\nDetailed results:")
    for example_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status} {example_name}")

    if successful == total:
        print(f"\n🎉 All examples completed successfully!")
        return 0
    else:
        print(f"\n⚠️  Some examples failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
