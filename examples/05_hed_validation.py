#!/usr/bin/env python3
"""
HED Validation Example
======================

This example demonstrates how to validate HED annotations in NWB files using
the HedNWBValidator class.

"""

from pynwb import NWBFile
from pynwb.core import DynamicTable, VectorData
from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from ndx_events import EventsTable, TimestampVectorData
from hed.errors import ErrorHandler
from datetime import datetime

def create_test_data():
    """Create NWB file with both valid and invalid HED annotations for testing"""
    print("Creating test data with valid and invalid HED annotations...")
    
    nwbfile = NWBFile(
        session_description="HED validation test data",
        identifier="hed_validation_example",
        session_start_time=datetime.now()
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
    nwbfile.add_lab_meta_data(hed_metadata)

    # Table 1: Valid HED annotations
    valid_table = DynamicTable(
        name="valid_events",
        description="Events with valid HED annotations",
        columns=[
            VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0]),
            HedTags(data=[
                "Sensory-event, Visual-presentation",
                "Agent-action, Participant-response",
                "Experimental-trial"
            ])
        ]
    )

    # Table 2: Invalid HED annotations
    invalid_table = DynamicTable(
        name="invalid_events",
        description="Events with invalid HED annotations",
        columns=[
            VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0]),
            HedTags(data=[
                "InvalidTag123",  # Not a valid HED tag
                "NonExistentEvent",  # Not in HED schema
                "BadTag/WithSlash"  # Invalid syntax
            ])
        ]
    )

    # Table 3: Mixed valid/invalid
    mixed_table = DynamicTable(
        name="mixed_events",
        description="Events with mixed HED annotations",
        columns=[
            VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0, 4.0]),
            HedTags(data=[
                "Sensory-event",  # Valid
                "InvalidMixedTag",  # Invalid
                "Agent-action, Button-press",  # Valid
                "AnotherBadTag"  # Invalid
            ])
        ]
    )

    # Table 4: HedValueVector with issues
    value_vector_table = DynamicTable(
        name="value_vector_events",
        description="Events with HedValueVector",
        columns=[
            VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
            HedValueVector(
                name="reaction_time",
                description="Response times",
                data=[0.5, 0.7, 0.3],
                hed="Behavioral-evidence, InvalidValueTag/#"  # Contains invalid tag
            )
        ]
    )

    # Add tables to NWB file
    nwbfile.add_acquisition(valid_table)
    nwbfile.add_acquisition(invalid_table)
    nwbfile.add_acquisition(mixed_table)
    nwbfile.add_acquisition(value_vector_table)

    return nwbfile, hed_metadata

def validate_individual_components(validator, nwbfile):
    """Demonstrate validation of individual components"""
    print("\n1. Validating individual table components...")
    
    # Get tables from NWB file
    valid_table = nwbfile.acquisition["valid_events"]
    invalid_table = nwbfile.acquisition["invalid_events"]
    mixed_table = nwbfile.acquisition["mixed_events"]
    
    # Validate individual HedTags columns
    print("\n   Validating HedTags columns:")
    
    # Valid column
    valid_column = valid_table["HED"]
    valid_issues = validator.validate_vector(valid_column)
    print(f"   - Valid column: {len(valid_issues)} issues found")
    
    # Invalid column
    invalid_column = invalid_table["HED"]
    invalid_issues = validator.validate_vector(invalid_column)
    print(f"   - Invalid column: {len(invalid_issues)} issues found")
    if invalid_issues:
        print("     Sample issues:")
        for i, issue in enumerate(invalid_issues[:2]):  # Show first 2 issues
            print(f"       {i+1}. {issue.get('message', 'Unknown error')}")
    
    # Mixed column
    mixed_column = mixed_table["HED"]
    mixed_issues = validator.validate_vector(mixed_column)
    print(f"   - Mixed column: {len(mixed_issues)} issues found")

def validate_tables(validator, nwbfile):
    """Demonstrate table-level validation"""
    print("\n2. Validating complete tables...")
    
    tables = [
        ("valid_events", "Valid table"),
        ("invalid_events", "Invalid table"),
        ("mixed_events", "Mixed table"),
        ("value_vector_events", "HedValueVector table")
    ]
    
    for table_name, description in tables:
        table = nwbfile.acquisition[table_name]
        issues = validator.validate_table(table)
        print(f"   - {description}: {len(issues)} issues found")
        
        if issues:
            # Show error breakdown
            error_count = sum(1 for issue in issues if issue.get('severity', 0) == 1)
            warning_count = len(issues) - error_count
            print(f"     (Errors: {error_count}, Warnings: {warning_count})")

def validate_events_table(validator):
    """Demonstrate EventsTable validation"""
    print("\n3. Validating EventsTable...")
    
    # Create EventsTable with HED issues
    events_table = EventsTable(
        name="test_events",
        description="EventsTable with validation issues"
    )
    
    events_table.add_column("timestamp", TimestampVectorData(
        name="timestamp",
        description="Event timestamps",
        data=[1.0, 2.0, 3.0]
    ))
    
    events_table.add_column("HED", HedTags(
        name="HED",
        description="Event HED annotations",
        data=[
            "Sensory-event",  # Valid
            "InvalidEventTag",  # Invalid
            "Agent-action, Press"  # Valid
        ]
    ))
    
    # Validate EventsTable
    issues = validator.validate_events(events_table)
    print(f"   - EventsTable: {len(issues)} issues found")
    
    if issues:
        print("     Sample issues:")
        for i, issue in enumerate(issues[:2]):
            row = issue.get('ec_row', 'unknown')
            message = issue.get('message', 'Unknown error')
            print(f"       Row {row}: {message}")

def validate_entire_file(validator, nwbfile):
    """Demonstrate file-level validation"""
    print("\n4. Validating entire NWB file...")
    
    # Validate the entire file
    all_issues = validator.validate_file(nwbfile)
    
    print(f"   - Total issues found: {len(all_issues)}")
    
    if all_issues:
        # Categorize issues
        error_count = sum(1 for issue in all_issues if issue.get('severity', 0) == 1)
        warning_count = len(all_issues) - error_count
        
        print(f"     Errors: {error_count}")
        print(f"     Warnings: {warning_count}")
        
        # Show issues by table
        table_issues = {}
        for issue in all_issues:
            table_name = issue.get('ec_filename', 'unknown')
            if table_name not in table_issues:
                table_issues[table_name] = []
            table_issues[table_name].append(issue)
        
        print("     Issues by table:")
        for table_name, issues in table_issues.items():
            print(f"       {table_name}: {len(issues)} issues")

def demonstrate_custom_error_handler(validator, nwbfile):
    """Demonstrate using custom ErrorHandler"""
    print("\n5. Using custom ErrorHandler...")
    
    # Create custom error handler that includes warnings
    error_handler = ErrorHandler(check_for_warnings=True)
    
    # Validate with custom handler
    invalid_table = nwbfile.acquisition["invalid_events"]
    issues = validator.validate_table(invalid_table, error_handler)
    
    print(f"   - Issues with warnings enabled: {len(issues)}")
    
    # Compare with default handler (warnings disabled)
    issues_no_warnings = validator.validate_table(invalid_table)
    print(f"   - Issues with warnings disabled: {len(issues_no_warnings)}")

def main():
    # Create test data
    nwbfile, hed_metadata = create_test_data()
    
    # Create validator
    print("Creating HED validator...")
    validator = HedNWBValidator(hed_metadata)
    print(f"Validator schema version: {validator.hed_metadata.hed_schema_version}")
    
    # Demonstrate different validation approaches
    validate_individual_components(validator, nwbfile)
    validate_tables(validator, nwbfile)
    validate_events_table(validator)
    validate_entire_file(validator, nwbfile)
    demonstrate_custom_error_handler(validator, nwbfile)
    
    print(f"\n✓ HED validation demonstration complete!")
    print("Use the validation results to identify and fix HED annotation issues.")
    
    return nwbfile, validator

if __name__ == "__main__":
    nwbfile, validator = main()
