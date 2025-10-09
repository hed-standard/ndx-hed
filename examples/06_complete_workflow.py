#!/usr/bin/env python3
"""
Complete Workflow Example
=========================

This example demonstrates a complete workflow using the ndx-hed extension:
1. Create NWB file with HED metadata
2. Add various types of HED annotations
3. Validate the annotations
4. Save and reload the file
5. Verify validation consistency

"""

from pynwb import NWBHDF5IO
from pynwb.core import DynamicTable, VectorData
from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from ndx_events import EventsTable, NdxEventsNWBFile, DurationVectorData
from datetime import datetime, timezone
import tempfile
import os
import numpy as np


def create_comprehensive_nwb_file():
    """Create a comprehensive NWB file with all types of HED annotations"""
    print("1. Creating comprehensive NWB file with HED annotations...")

    # Create NWB file with HED metadata
    nwbfile = NdxEventsNWBFile(
        session_description="Complete HED workflow demonstration",
        identifier="complete_hed_workflow",
        session_start_time=datetime.now(timezone.utc),
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
    nwbfile.add_lab_meta_data(hed_metadata)
    print(f"   - Added HED schema version: {hed_metadata.hed_schema_version}")

    # Add trials with HED annotations
    nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")

    trial_data = [
        (0.0, 2.0, "Experimental-trial, (Sensory-event, Visual-presentation, Red)"),
        (3.0, 5.0, "Experimental-trial, (Agent-action, Participant-response, Button-press)"),
        (6.0, 8.0, "Experimental-trial, (Sensory-event, Auditory-presentation, Tone)"),
        (9.0, 11.0, "Experimental-trial, Rest"),
    ]

    for start, stop, hed_annotation in trial_data:
        nwbfile.add_trial(start_time=start, stop_time=stop, HED=hed_annotation)

    print(f"   - Added {len(trial_data)} trials with HED annotations")

    # Create behavioral events table using DynamicTable rather than the EventsTable class
    behavioral_table = DynamicTable(
        name="behavioral_events",
        description="Behavioral events during the experiment",
        columns=[
            VectorData(name="event_time", description="Time of event", data=[1.5, 3.2, 5.8, 7.1, 9.5]),
            VectorData(
                name="event_type",
                description="Type of event",
                data=["stimulus_onset", "response", "stimulus_onset", "response", "pause"],
            ),
            HedTags(
                data=[
                    "Sensory-event, Visual-presentation, (Red, Circle)",
                    "Agent-action, Participant-response, Button-press",
                    "Sensory-event, Auditory-presentation, Tone",
                    "Agent-action, Participant-response, Button-press",
                    "Pause",
                ]
            ),
            HedValueVector(
                name="reaction_time",
                description="Reaction time in seconds",
                data=[np.nan, 0.5, np.nan, 0.3, np.nan],
                hed="Behavioral-evidence, Label/Reaction-time, Time-value/# s",
            ),
        ],
    )
    nwbfile.add_acquisition(behavioral_table)
    print(f"   - Added behavioral events table with {len(behavioral_table)} events")

    # Create EventsTable with comprehensive annotations
    events_table = EventsTable(
        name="comprehensive_events", description="Comprehensive events with multiple HED annotation types"
    )

    events_table.add_column(
        name="duration", description="Event durations", data=[], col_cls=DurationVectorData  # Start empty
    )

    events_table.add_column(
        name="HED", description="Event-specific HED annotations", data=[], col_cls=HedTags  # Start empty
    )

    events_table.add_column(
        name="stimulus_contrast",
        description="Stimulus contrast with background",
        data=[],  # Start empty
        col_cls=HedValueVector,
        hed="Luminance-contrast/#",
    )

    # Add rows of event data
    events = [
        {"timestamp": 1.0, "duration": 0.5, "HED": "(Sensory-event, Visual-presentation)", "stimulus_contrast": 0.7},
        {"timestamp": 2.5, "duration": 0.3, "HED": "(Agent-action, Participant-response)", "stimulus_contrast": 0.0},
        {"timestamp": 4.0, "duration": 0.8, "HED": "(Sensory-event, Auditory-presentation)", "stimulus_contrast": 0.9},
        {"timestamp": 5.5, "duration": 0.4, "HED": "(Agent-action, Participant-response)", "stimulus_contrast": 0.0},
        {"timestamp": 7.0, "duration": 0.6, "HED": "Pause", "stimulus_contrast": 0.0},
        {"timestamp": 8.5, "duration": 0.2, "HED": "Label/End-session", "stimulus_contrast": 0.0},
    ]

    for event in events:
        events_table.add_row(event)

    nwbfile.add_events_table(events_table)
    print(f"   - Added comprehensive events table with {len(events_table)} events")

    return nwbfile


def validate_annotations(nwbfile):
    """Validate all HED annotations in the NWB file.

    Args:
        nwbfile: An in-memory NWBFile object or an open NWB file

    Returns:
        list: List of validation issues
    """
    # Get HED metadata and create validator
    hed_metadata = nwbfile.lab_meta_data["hed_schema"]
    validator = HedNWBValidator(hed_metadata)

    # Validate the entire file
    issues = validator.validate_file(nwbfile)

    return issues


def get_context(issue):
    """Extract context information from a validation issue."""
    context_string = f"[{issue.get('ec_filename', 'unknown_location')}]"
    column = issue.get("ec_column", "")
    if column:
        context_string += f"(Column: {column})"
    row = issue.get("ec_row", "")
    if row:
        context_string += f"(Row: {row})"

    return context_string


def print_issues(title, issues):
    """Print validation issues with formatting.

    Args:
        title: Title to display for this set of issues
        issues: List of validation issues to display
    """
    print(f"\n{title}")
    print(f"   - Total validation issues: {len(issues)}")

    if issues:
        # Categorize and display issues
        errors = [issue for issue in issues if issue.get("severity", 0) == 1]
        warnings = [issue for issue in issues if issue.get("severity", 0) == 2]

        print(f"     Errors: {len(errors)}")
        print(f"     Warnings: {len(warnings)}")

        if errors:
            print("     Error examples:")
            for i, error in enumerate(errors[:3]):  # Show first 3 errors
                message = error.get("message", "Unknown error")
                print(f"       {i+1}. [{get_context(error)}] {message}")
    else:
        print("   ✓ All HED annotations are valid!")


def save_and_reload_file(nwbfile):
    """Save the file and reload it to test persistence"""
    print("\n3. Testing file save/reload cycle...")

    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".nwb", delete=False) as temp_file:
        temp_filename = temp_file.name

    try:
        # Save the file
        with NWBHDF5IO(temp_filename, "w") as io:
            io.write(nwbfile)
        print(f"   - Saved NWB file: {os.path.basename(temp_filename)}")

        # Reload and validate while file is open, then return just basic info
        with NWBHDF5IO(temp_filename, "r", load_namespaces=True) as io:
            reloaded_nwbfile = io.read()
            print("   - Reloaded NWB file successfully")

            # Check that HED metadata is preserved
            original_schema = nwbfile.lab_meta_data["hed_schema"].hed_schema_version
            reloaded_schema = reloaded_nwbfile.lab_meta_data["hed_schema"].hed_schema_version

            if original_schema == reloaded_schema:
                print(f"   ✓ HED schema version preserved: {reloaded_schema}")
            else:
                print(f"   ✗ Schema version mismatch: {original_schema} -> {reloaded_schema}")

            # Validate while file is open
            reloaded_issues = validate_annotations(reloaded_nwbfile)

            return reloaded_issues

    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def verify_validation_consistency(original_issues, reloaded_issues):
    """Verify that validation results are consistent after file I/O.

    Args:
        original_issues: List of issues from original in-memory file
        reloaded_issues: List of issues from reloaded file
    """
    print("\n4. Verifying validation consistency...")

    print(f"   - Original file issues: {len(original_issues)}")
    print(f"   - Reloaded file issues: {len(reloaded_issues)}")

    if len(original_issues) == len(reloaded_issues):
        print("   ✓ Validation consistency maintained")

        # Check issue details match
        if len(original_issues) > 0:
            original_codes = set(issue.get("code", "") for issue in original_issues)
            reloaded_codes = set(issue.get("code", "") for issue in reloaded_issues)

            if original_codes == reloaded_codes:
                print("   ✓ Issue types are identical")
            else:
                print("   ! Issue types differ slightly")
                print(f"     Original: {sorted(original_codes)}")
                print(f"     Reloaded: {sorted(reloaded_codes)}")
    else:
        print("   ✗ Validation inconsistency detected")
        print(f"     Original had {len(original_issues)} issues")
        print(f"     Reloaded had {len(reloaded_issues)} issues")

    return len(original_issues), len(reloaded_issues)


def display_summary(nwbfile):
    """Display a summary of the created file"""
    print("\n5. File Summary:")
    print(f"   - Session: {nwbfile.session_description}")
    print(f"   - Identifier: {nwbfile.identifier}")
    print(f"   - HED Schema: {nwbfile.lab_meta_data['hed_schema'].hed_schema_version}")
    print(f"   - Trials: {len(nwbfile.trials) if nwbfile.trials is not None else 0}")
    print(f"   - Acquisition objects: {len(nwbfile.acquisition)}")

    print("\n   Acquisition tables:")
    for name, obj in nwbfile.acquisition.items():
        if hasattr(obj, "colnames"):  # For EventsTable and other dynamic tables
            colnames = list(obj.colnames)
            hed_columns = [col for col in colnames if col == "HED"]
            # Count HedValueVector columns by checking column objects
            value_vector_columns = []
            for col in colnames:
                try:
                    col_obj = getattr(obj, col, None)
                    if col_obj and hasattr(col_obj, "hed"):
                        value_vector_columns.append(col)
                except Exception:
                    pass  # Skip if column access fails

            print(
                f"     - {name}: {len(obj)} rows, "
                f"{len(colnames)} columns (HED: {len(hed_columns)}, ValueVector: {len(value_vector_columns)})"
            )
        else:
            print(f"     - {name}: {type(obj).__name__}")

    # Check for events tables (accessed via nwbfile.events)
    print(f"\n   Events tables: {len(nwbfile.events)}")
    for name, events_table in nwbfile.events.items():
        if hasattr(events_table, "colnames"):
            colnames = list(events_table.colnames)
            hed_columns = [col for col in colnames if col == "HED"]
            value_vector_columns = []
            for col in colnames:
                try:
                    col_obj = getattr(events_table, col, None)
                    if col_obj and hasattr(col_obj, "hed"):
                        value_vector_columns.append(col)
                except Exception:
                    pass

            print(
                f"     - {name}: {len(events_table)} rows, "
                f"{len(colnames)} columns (HED: {len(hed_columns)}, ValueVector: {len(value_vector_columns)})"
            )


def main():
    """Execute the complete workflow"""
    print("=== Complete HED Workflow Demonstration ===\n")

    # Step 1: Create comprehensive NWB file
    nwbfile = create_comprehensive_nwb_file()

    # Step 2: Validate annotations
    original_issues = validate_annotations(nwbfile)
    print_issues("2. Validating HED annotations...", original_issues)

    # Step 3: Save and reload, validate while file is open
    reloaded_issues = save_and_reload_file(nwbfile)

    # Step 4: Verify consistency
    verify_validation_consistency(original_issues, reloaded_issues)

    # Step 5: Display summary
    display_summary(nwbfile)

    print("\n✓ Complete HED workflow demonstration finished!")
    print("This example shows the full cycle of creating, validating, and")
    print("persisting NWB files with comprehensive HED annotations.")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
