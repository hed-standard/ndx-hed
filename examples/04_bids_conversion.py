#!/usr/bin/env python3
"""
BIDS to NWB Conversion Example
==============================

This example demonstrates how to convert BIDS events files with HED annotations
to NWB EventsTable format using the ndx-hed utilities, and how to export an
NWB table back to a BIDS events file and sidecar.

"""

import json
import os
import tempfile
from datetime import datetime, timezone

import pandas as pd
from pynwb import NWBFile

from ndx_hed import HedLabMetaData
from ndx_hed.utils.bids2nwb import extract_meanings, get_bids_tabular, get_events_table, read_bids_tsv
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator


def create_sample_bids_data():
    """Create sample BIDS events and sidecar data for demonstration"""
    print("Creating sample BIDS data...")

    # Sample BIDS events.tsv data
    events_data = {
        "onset": [1.0, 2.5, 4.0, 5.5, 7.0],
        "duration": [0.5, 0.3, 0.8, 0.4, 0.6],
        "event_type": ["stimulus", "response", "stimulus", "response", "pause"],
        "trial_number": [1, 1, 2, 2, 2],
        "stimulus_intensity": [0.7, "n/a", 0.9, "n/a", "n/a"],
    }
    events_df = pd.DataFrame(events_data)

    # Sample BIDS events.json sidecar
    events_sidecar = {
        "event_type": {
            "Description": "Type of event in the experiment",
            "Levels": {
                "stimulus": "Visual stimulus presentation",
                "response": "Participant button press response",
                "pause": "Inter-trial pause period",
            },
            "HED": {
                "stimulus": "Sensory-event, Visual-presentation",
                "response": "Agent-action, Participant-response, (Press, Push-button)",
                "pause": "Pause",
            },
        },
        "trial_number": {"Description": "Trial number in the experiment", "HED": "Experimental-trial/#"},
        "stimulus_intensity": {
            "Description": "Contrast of the visual stimulus with the background",
            "HED": "Luminance-contrast/#",
        },
    }

    return events_df, events_sidecar


def demonstrate_bids_conversion():
    """Convert BIDS events to EventsTable"""
    print("\nConverting BIDS events to EventsTable...")

    # Get sample BIDS data
    events_df, events_sidecar = create_sample_bids_data()

    print("Sample BIDS events data:")
    print(events_df.to_string(index=False))

    print("\nSample BIDS sidecar structure:")
    for column, info in events_sidecar.items():
        print(f"  {column}:")
        if "HED" in info:
            print(f"    HED: {info['HED']}")
        if "Levels" in info:
            print(f"    Levels: {list(info['Levels'].keys())}")

    # Extract the HED of the categorical and value columns from the sidecar JSON
    meanings = extract_meanings(events_sidecar)
    print(
        f"\nExtracted {len(meanings['categorical'])} categorical column(s) and "
        f"{len(meanings['value'])} value column(s) from the sidecar"
    )

    # Convert to EventsTable; each categorical column gets a MeaningsTable
    events_table = get_events_table(
        name="task_events",
        description="Task events converted from BIDS with HED annotations",
        df=events_df,
        meanings=meanings,
    )

    print("\n[OK] Successfully converted to EventsTable:")
    print(f"  - Number of events: {len(events_table)}")
    print(f"  - Columns: {events_table.colnames}")

    return events_table


def save_bids_files(events_df, events_sidecar, directory, base_name):
    """Write a BIDS events file and its JSON sidecar into a directory"""
    events_filename = os.path.join(directory, f"{base_name}_events.tsv")
    sidecar_filename = os.path.join(directory, f"{base_name}_events.json")

    # Write LF explicitly: on Windows, text mode and the pandas default line terminator would otherwise produce CRLF.
    events_df.to_csv(events_filename, sep="\t", index=False, lineterminator="\n")
    with open(sidecar_filename, "w", newline="\n") as sidecar_file:
        json.dump(events_sidecar, sidecar_file, indent=2)

    return events_filename, sidecar_filename


def load_bids_files(events_filename, sidecar_filename, name, description):
    """Read a BIDS events file and its JSON sidecar into an EventsTable"""
    # Read the TSV as hedtools reads it (values exactly as written)
    events_df = read_bids_tsv(events_filename)
    with open(sidecar_filename) as f:
        events_sidecar = json.load(f)
    return get_events_table(name=name, description=description, df=events_df, meanings=extract_meanings(events_sidecar))


def demonstrate_file_conversion():
    """Demonstrate conversion from actual BIDS files"""
    print("\nDemonstrating file-based BIDS conversion...")

    events_df, events_sidecar = create_sample_bids_data()

    # The temporary directory and the files in it are removed when the block ends
    with tempfile.TemporaryDirectory() as directory:
        events_filename, sidecar_filename = save_bids_files(events_df, events_sidecar, directory, "sub-01_task-demo")
        print(f"  - Events file: {os.path.basename(events_filename)}")
        print(f"  - Sidecar file: {os.path.basename(sidecar_filename)}")

        events_table = load_bids_files(
            events_filename, sidecar_filename, "file_based_events", "Events loaded from BIDS files"
        )

    print(f"[OK] File-based conversion successful: {len(events_table)} events")
    return events_table


def demonstrate_nwb_to_bids(events_table, hed_metadata, validator):
    """Export an NWB table to BIDS files, read them back, and check that nothing was lost"""
    print("\nExporting the EventsTable back to BIDS (NWB -> BIDS -> NWB)...")

    # get_bids_tabular returns the BIDS dataframe and the JSON sidecar; the sidecar holds the
    # HED of the HedValueVector columns and of each MeaningsTable (and any definitions in hed_metadata)
    bids_df, bids_sidecar = get_bids_tabular(events_table, hed_metadata)
    print(f"  - BIDS columns: {list(bids_df.columns)}")
    print(f"  - Sidecar entries with HED: {[name for name, info in bids_sidecar.items() if 'HED' in info]}")

    with tempfile.TemporaryDirectory() as directory:
        events_filename, sidecar_filename = save_bids_files(bids_df, bids_sidecar, directory, "sub-01_task-export")
        reloaded = load_bids_files(events_filename, sidecar_filename, events_table.name, events_table.description)

    # Export the reloaded table again: the round trip should give the same sidecar and data
    reloaded_df, reloaded_sidecar = get_bids_tabular(reloaded, hed_metadata)
    print(f"  - Sidecar unchanged by the round trip: {reloaded_sidecar == bids_sidecar}")
    print(f"  - Data unchanged by the round trip: {reloaded_df.astype(str).equals(bids_df.astype(str))}")

    original_issues = validator.validate_table(events_table)
    reloaded_issues = validator.validate_table(reloaded)
    print(f"  - Validation issues before / after: {len(original_issues)} / {len(reloaded_issues)}")


def main():
    # Create NWB file with HED metadata
    nwbfile = NWBFile(
        session_description="BIDS to NWB conversion example",
        identifier="bids_conversion_example",
        session_start_time=datetime.now(timezone.utc),
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
    nwbfile.add_lab_meta_data(hed_metadata)
    validator = HedNWBValidator(hed_metadata)

    # Demonstrate different conversion approaches
    events_table1 = demonstrate_bids_conversion()
    events_table2 = demonstrate_file_conversion()

    # Add EventsTables to NWB file
    nwbfile.add_events_table(events_table1)
    nwbfile.add_events_table(events_table2)

    # And back from NWB to BIDS
    demonstrate_nwb_to_bids(events_table1, hed_metadata, validator)

    print("\n[OK] Successfully created NWB file with BIDS-converted events!")
    print(f"  - Memory-based conversion: {len(events_table1)} events")
    print(f"  - File-based conversion: {len(events_table2)} events")

    # Validate the annotations (05_hed_validation.py shows validation in detail)
    issues = validator.validate_file(nwbfile)
    print(f"  - HED validation issues: {len(issues)}")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
