#!/usr/bin/env python3
"""Quick test script to verify the new definitions parameter works."""

from ndx_hed.hed_lab_metadata import HedLabMetaData

# Test creating HedLabMetaData without definitions
print("Testing HedLabMetaData without definitions...")
hed_meta1 = HedLabMetaData(hed_schema_version="8.4.0")
print(f"Schema version: {hed_meta1.get_hed_schema_version()}")
print(f"Definitions: {hed_meta1.get_definitions()}")

# Test creating HedLabMetaData with definitions
print("\nTesting HedLabMetaData with definitions...")
test_definitions = "Apple/Blue: This is a test definition.\nOrange/Red: Another test definition."
hed_meta2 = HedLabMetaData(hed_schema_version="8.4.0", definitions=test_definitions)
print(f"Schema version: {hed_meta2.get_hed_schema_version()}")
print(f"Definitions: {hed_meta2.get_definitions()}")

print("\nAll tests completed successfully!")
