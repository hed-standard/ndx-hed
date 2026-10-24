#!/usr/bin/env python3
"""
Complete Workflow Example
=========================

This example demonstrates a complete workflow using the ndx-hed extension:
1. Create NWB file with HED metadata
2. Add the three kinds of HED annotation: per-row (HedTags), value templates
   (HedValueVector), and categorical (a MeaningsTable with a HED column)
3. Validate the annotations and show how each row's HED is assembled
4. Save and reload the file
5. Verify validation consistency

"""

import io
import json
import os
import tempfile
from datetime import datetime, timezone

import numpy as np
from hdmf.common import MeaningsTable
from hed.errors import ErrorSeverity, get_printable_issue_string
from hed.models import Sidecar, TabularInput
from pynwb import NWBHDF5IO, NWBFile
from pynwb.core import DynamicTable, VectorData
from pynwb.event import DurationVectorData, EventsTable

from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.bids2nwb import get_bids_tabular
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator


def create_comprehensive_events():
    """Create an EventsTable that uses all three kinds of HED annotation"""
    events_table = EventsTable(
        name="comprehensive_events", description="Comprehensive events with multiple HED annotation types"
    )

    events_table.add_column(name="duration", description="Event durations", data=[], col_cls=DurationVectorData)

    # Categorical column: a plain VectorData whose values get their HED from a MeaningsTable (below)
    events_table.add_column(name="event_type", description="Kind of event", data=[])

    # Per-row HED: the details that differ from row to row
    events_table.add_column(name="HED", description="Event-specific HED annotations", data=[], col_cls=HedTags)

    # Value template: each value is substituted for the # (a missing value contributes nothing)
    events_table.add_column(
        name="stimulus_contrast",
        description="Stimulus contrast with background",
        data=[],
        col_cls=HedValueVector,
        hed="Luminance-contrast/#",
    )

    # Add rows of event data
    events = [
        {"timestamp": 1.0, "duration": 0.5, "event_type": "visual", "HED": "(Red, Circle)", "stimulus_contrast": 0.7},
        {
            "timestamp": 2.5,
            "duration": 0.3,
            "event_type": "response",
            "HED": "(Press, Push-button)",
            "stimulus_contrast": np.nan,
        },
        {"timestamp": 4.0, "duration": 0.8, "event_type": "visual", "HED": "(Blue, Square)", "stimulus_contrast": 0.9},
        {
            "timestamp": 5.5,
            "duration": 0.4,
            "event_type": "response",
            "HED": "(Press, Push-button)",
            "stimulus_contrast": np.nan,
        },
        {"timestamp": 7.0, "duration": 0.6, "event_type": "pause", "HED": "", "stimulus_contrast": np.nan},
        {"timestamp": 8.5, "duration": 0.2, "event_type": "end", "HED": "", "stimulus_contrast": np.nan},
    ]

    for event in events:
        events_table.add_row(event)

    # The MeaningsTable gives each event_type value its meaning and its HED (the target column must exist)
    meanings = MeaningsTable(target=events_table["event_type"], description="Meanings and HED of the event types")
    categories = [
        ("visual", "Visual stimulus presentation", "Sensory-event, Visual-presentation"),
        ("response", "Participant button press", "Agent-action, Participant-response"),
        ("pause", "Inter-trial pause", "Pause"),
        ("end", "End of the session", "Label/End-session"),
    ]
    for value, meaning, _hed in categories:
        meanings.add_row(value=value, meaning=meaning)
    meanings.add_column(
        name="HED", description="HED of each event type", data=[hed for _, _, hed in categories], col_cls=HedTags
    )
    events_table.add_meanings_table(meanings)

    return events_table


def create_comprehensive_nwb_file():
    """Create a comprehensive NWB file with all types of HED annotations"""
    print("1. Creating comprehensive NWB file with HED annotations...")

    # Create NWB file with HED metadata
    nwbfile = NWBFile(
        session_description="Complete HED workflow demonstration",
        identifier="complete_hed_workflow",
        session_start_time=datetime.now(timezone.utc),
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.5.0")
    nwbfile.add_lab_meta_data(hed_metadata)
    print(f"   - Added HED schema version: {hed_metadata.hed_schema_version}")

    # Add trials with HED annotations
    nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")

    trial_data = [
        (0.0, 2.0, "Experimental-trial, (Sensory-event, Visual-presentation, Red)"),
        (3.0, 5.0, "Experimental-trial, (Agent-action, Participant-response, (Press, Push-button))"),
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
                    "Agent-action, Participant-response, (Press, Push-button)",
                    "Sensory-event, Auditory-presentation, Tone",
                    "Agent-action, Participant-response, (Press, Push-button)",
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

    # Create EventsTable with all three kinds of HED annotation
    events_table = create_comprehensive_events()
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
        errors = [issue for issue in issues if issue["severity"] == ErrorSeverity.ERROR]
        warnings = [issue for issue in issues if issue["severity"] == ErrorSeverity.WARNING]

        print(f"     Errors: {len(errors)}")
        print(f"     Warnings: {len(warnings)}")

        # get_printable_issue_string (hedtools) shows each issue with its file, table, column, and row
        print(get_printable_issue_string(issues))
    else:
        print("   [OK] All HED annotations are valid!")


def show_assembled_hed(nwbfile):
    """Show the HED of each event row once its per-row, categorical, and value HED are combined"""
    print("\n   Assembled HED of the comprehensive events (what validation checks row by row):")

    # get_bids_tabular gives the table as a BIDS dataframe and sidecar; hedtools assembles each row from them
    events_table = nwbfile.events["comprehensive_events"]
    bids_df, bids_sidecar = get_bids_tabular(events_table, nwbfile.lab_meta_data["hed_schema"])
    tabular = TabularInput(bids_df, sidecar=Sidecar(io.StringIO(json.dumps(bids_sidecar))))
    for row, hed_string in enumerate(tabular.series_a):
        print(f"     Row {row}: {hed_string}")


def save_and_reload_file(nwbfile):
    """Save the file and reload it to test persistence"""
    print("\n3. Testing file save/reload cycle...")

    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".nwb", delete=False) as temp_file:
        temp_filename = temp_file.name

    try:
        # Save the file
        with NWBHDF5IO(temp_filename, "w") as io_file:
            io_file.write(nwbfile)
        print(f"   - Saved NWB file: {os.path.basename(temp_filename)}")

        # Reload and validate while file is open, then return just basic info
        with NWBHDF5IO(temp_filename, "r", load_namespaces=True) as io_file:
            reloaded_nwbfile = io_file.read()
            print("   - Reloaded NWB file successfully")

            # Check that HED metadata is preserved
            original_schema = nwbfile.lab_meta_data["hed_schema"].hed_schema_version
            reloaded_schema = reloaded_nwbfile.lab_meta_data["hed_schema"].hed_schema_version

            if original_schema == reloaded_schema:
                print(f"   [OK] HED schema version preserved: {reloaded_schema}")
            else:
                print(f"   [FAIL] Schema version mismatch: {original_schema} -> {reloaded_schema}")

            # Check that the categorical HED is preserved
            meanings = reloaded_nwbfile.events["comprehensive_events"].get_meanings_for_column("event_type")
            print(f"   [OK] MeaningsTable preserved: {meanings.name} with {len(meanings)} values")

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
        print("   [OK] Validation consistency maintained")

        # Check issue details match
        if len(original_issues) > 0:
            original_codes = {issue.get("code", "") for issue in original_issues}
            reloaded_codes = {issue.get("code", "") for issue in reloaded_issues}

            if original_codes == reloaded_codes:
                print("   [OK] Issue types are identical")
            else:
                print("   ! Issue types differ slightly")
                print(f"     Original: {sorted(original_codes)}")
                print(f"     Reloaded: {sorted(reloaded_codes)}")
    else:
        print("   [FAIL] Validation inconsistency detected")
        print(f"     Original had {len(original_issues)} issues")
        print(f"     Reloaded had {len(reloaded_issues)} issues")

    return len(original_issues), len(reloaded_issues)


def describe_table(name, table):
    """Return one line describing a table and its HED columns"""
    columns = [table[col] for col in table.colnames]
    hed_columns = sum(1 for col in columns if isinstance(col, HedTags))
    value_columns = sum(1 for col in columns if isinstance(col, HedValueVector))
    categorical_columns = sum(1 for col in table.colnames if table.get_meanings_for_column(col) is not None)
    return (
        f"     - {name}: {len(table)} rows, {len(columns)} columns "
        f"(HED: {hed_columns}, HedValueVector: {value_columns}, categorical: {categorical_columns})"
    )


def display_summary(nwbfile):
    """Display a summary of the created file"""
    print("\n5. File Summary:")
    print(f"   - Session: {nwbfile.session_description}")
    print(f"   - Identifier: {nwbfile.identifier}")
    print(f"   - HED Schema: {nwbfile.lab_meta_data['hed_schema'].hed_schema_version}")
    print(f"   - Trials: {len(nwbfile.trials) if nwbfile.trials is not None else 0}")

    print(f"\n   Acquisition tables: {len(nwbfile.acquisition)}")
    for name, table in nwbfile.acquisition.items():
        print(describe_table(name, table))

    print(f"\n   Events tables: {len(nwbfile.events)}")
    for name, table in nwbfile.events.items():
        print(describe_table(name, table))


def main():
    """Execute the complete workflow"""
    print("=== Complete HED Workflow Demonstration ===\n")

    # Step 1: Create comprehensive NWB file
    nwbfile = create_comprehensive_nwb_file()

    # Step 2: Validate annotations, and show what validation sees for each event
    original_issues = validate_annotations(nwbfile)
    print_issues("2. Validating HED annotations...", original_issues)
    show_assembled_hed(nwbfile)

    # Step 3: Save and reload, validate while file is open
    reloaded_issues = save_and_reload_file(nwbfile)

    # Step 4: Verify consistency
    verify_validation_consistency(original_issues, reloaded_issues)

    # Step 5: Display summary
    display_summary(nwbfile)

    print("\n[OK] Complete HED workflow demonstration finished!")
    print("This example shows the full cycle of creating, validating, and")
    print("persisting NWB files with comprehensive HED annotations.")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
