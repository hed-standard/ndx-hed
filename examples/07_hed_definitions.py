#!/usr/bin/env python3
"""
HED Definitions Example
======================

This example demonstrates how to use HED definitions with ndx-hed:
1. Creating custom HED definitions in HedLabMetaData
2. Using definitions in HED annotations
3. Validating definitions with the schema

"""
import pandas as pd
from hed.models.df_util import expand_defs
from pynwb import NWBFile
from pynwb.core import DynamicTable, VectorData
from ndx_hed import HedLabMetaData, HedTags
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from datetime import datetime


def create_file_with_definitions():
    """Example 1: Create NWB file with custom HED definitions"""
    print("1. Creating NWB file with custom HED definitions...")
    
    # Create NWB file
    nwbfile = NWBFile(
        session_description="HED definitions demonstration",
        identifier="hed_definitions_example",
        session_start_time=datetime.now(),
    )
    
    # Define custom HED definitions using valid HED tags
    # Note: For demonstration purposes, these are simplified definitions
    definitions = "(Definition/Go-stimulus, (Sensory-event, Visual-presentation)), (Definition/Stop-stimulus, (Sensory-event, Auditory-presentation)), (Definition/Correct-response, (Agent-action, Participant-response)), (Definition/Incorrect-response, (Agent-action, Participant-response)), (Definition/Response-time/#, (Time-interval/# s))"
    
    # Add HED schema metadata with definitions
    hed_metadata = HedLabMetaData(
        hed_schema_version="8.4.0", 
        definitions=definitions
    )
    nwbfile.add_lab_meta_data(hed_metadata)
    
    print(f"   - Added HED schema version: {hed_metadata.hed_schema_version}")
    print(f"   - Definitions count: {len(hed_metadata.get_definition_dict().defs)}")
    print(f"   - Definition names: {list(hed_metadata.get_definition_dict().defs.keys())}")
    
    return nwbfile, hed_metadata


def create_trials_with_definitions(nwbfile):
    """Example 2: Use definitions in trials table"""
    print("\n2. Creating trials table using custom definitions...")
    
    # Add HED column to trials
    nwbfile.add_trial_column(
        name="HED", 
        col_cls=HedTags, 
        data=[], 
        description="HED annotations using custom definitions"
    )
    
    # Trial data with custom definitions
    trials_data = [
        (0.0, 2.0, "Def/Go-stimulus, Experimental-trial"),
        (3.0, 5.0, "Def/Correct-response, Def/Response-time/0.45"),
        (6.0, 8.0, "Def/Stop-stimulus, Experimental-trial"), 
        (9.0, 11.0, "Def/Incorrect-response, Def/Response-time/0.89"),
        (12.0, 14.0, "Def/Go-stimulus, Def/Correct-response, Def/Response-time/0.32"),
    ]
    
    for start, stop, hed_annotation in trials_data:
        nwbfile.add_trial(start_time=start, stop_time=stop, HED=hed_annotation)
    
    print(f"   - Added {len(trials_data)} trials using custom definitions")
    return trials_data


def create_events_with_definitions(nwbfile):
    """Example 3: Use definitions in a custom events table"""
    print("\n3. Creating events table with definition-based annotations...")
    
    events_table = DynamicTable(
        name="experimental_events",
        description="Experimental events using HED definitions",
        columns=[
            VectorData(
                name="event_time", 
                description="Time of event", 
                data=[1.5, 3.2, 7.8, 10.1, 13.4]
            ),
            VectorData(
                name="stimulus_type", 
                description="Type of stimulus", 
                data=["go", "go", "stop", "go", "go"]
            ),
            VectorData(
                name="response_type", 
                description="Type of response", 
                data=["correct", "correct", "none", "incorrect", "correct"]
            ),
            VectorData(
                name="response_time", 
                description="Response time in seconds", 
                data=[0.45, 0.52, None, 0.89, 0.32]
            ),
            HedTags(
                data=[
                    "Def/Go-stimulus, Def/Correct-response, Def/Response-time/0.45",
                    "Def/Go-stimulus, Def/Correct-response, Def/Response-time/0.52",
                    "Def/Stop-stimulus",  # No response expected
                    "Def/Go-stimulus, Def/Incorrect-response, Def/Response-time/0.89", 
                    "Def/Go-stimulus, Def/Correct-response, Def/Response-time/0.32",
                ]
            ),
        ],
    )
    
    nwbfile.add_acquisition(events_table)
    print(f"   - Created events table with {len(events_table)} events")
    return events_table


def validate_definitions(hed_metadata, nwbfile):
    """Example 4: Validate the file with custom definitions"""
    print("\n4. Validating HED annotations with custom definitions...")
    
    # Create validator
    validator = HedNWBValidator(hed_metadata)
    
    # Validate entire file
    issues = validator.validate_file(nwbfile)
    
    print(f"   - Total validation issues: {len(issues)}")
    
    if issues:
        print("   - Issues found:")
        for issue in issues[:3]:  # Show first 3 issues
            print(f"     • {issue['message']}")
        if len(issues) > 3:
            print(f"     • ... and {len(issues) - 3} more issues")
    else:
        print("   ✓ All HED annotations are valid!")
    
    # Show definition validation specifically
    def_dict = hed_metadata.get_definition_dict()
    print(f"   - Definition dictionary issues: {len(def_dict.issues)}")
    
    return issues


def demonstrate_definition_expansion(hed_metadata):
    """Example 5: Show how definitions expand"""
    print("\n5. Demonstrating definition expansion...")
    

    schema = hed_metadata.get_hed_schema()
    print(f"   - Using HED schema version: {schema.version}")
    def_dict = hed_metadata.get_definition_dict()
    print(f"   - Definitions available: {list(def_dict.defs.keys())}")

    # Show how each definition expands
    sample_annotations = [
        "Def/Go-stimulus",
        "Def/Correct-response", 
        "Def/Response-time/0.45",
        "Def/Go-stimulus, Def/Correct-response"
    ]

    df = pd.DataFrame({"HED": sample_annotations})
    expand_defs(df, schema, def_dict)
    
    print("   Definition expansions:")
    for i, original_annotation in enumerate(sample_annotations):
        expanded_annotation = df.iloc[i]["HED"]  # Get the expanded value from the DataFrame
        print(f"     '{original_annotation}' → '{expanded_annotation}'")


def main():
    # Create file with definitions
    nwbfile, hed_metadata = create_file_with_definitions()
    
    # Use definitions in various contexts
    trials_data = create_trials_with_definitions(nwbfile)
    events_table = create_events_with_definitions(nwbfile)
    
    # Validate everything
    issues = validate_definitions(hed_metadata, nwbfile)
    print(f"")
    # Show definition expansion
    demonstrate_definition_expansion(hed_metadata)
    
    print(f"\n✓ Successfully demonstrated HED definitions!")
    print(f"  - Definitions created: {len(hed_metadata.get_definition_dict().defs)}")
    print(f"  - Trials with definitions: {len(trials_data)}")
    print(f"  - Events with definitions: {len(events_table)}")
    print(f"  - Validation issues: {len(issues)}")
    
    # Show available definitions
    print("\n  Available custom definitions:")
    for def_name in hed_metadata.get_definition_dict().defs.keys():
        def_entry = hed_metadata.get_definition_dict().defs[def_name]
        takes_value = " (takes value)" if def_entry.takes_value else ""
        print(f"    • {def_name}{takes_value}")
    
    return nwbfile


if __name__ == "__main__":
    nwbfile = main()