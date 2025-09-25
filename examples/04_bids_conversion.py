#!/usr/bin/env python3
"""
BIDS to NWB Conversion Example
==============================

This example demonstrates how to convert BIDS events files with HED annotations
to NWB EventsTable format using the ndx-hed utilities.

"""

import pandas as pd
import json
import tempfile
import os
from pynwb import NWBFile
from ndx_hed import HedLabMetaData
from ndx_hed.utils.bids2nwb import extract_meanings, get_events_table
from datetime import datetime


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
                "response": "Agent-action, Participant-response, Button-press",
                "pause": "Pause",
            },
        },
        "trial_number": {"Description": "Trial number in the experiment", "HED": "Experimental-trial/#"},
        "stimulus_intensity": {
            "Description": "Intensity of the visual stimulus",
            "HED": "Sensory-event, Luminance-attribute/#",
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

    # Extract meanings from sidecar JSON
    meanings = extract_meanings(events_sidecar)
    print(f"\nExtracted {len(meanings)} meanings tables from sidecar")

    # Convert to EventsTable
    events_table = get_events_table(
        name="task_events",
        description="Task events converted from BIDS with HED annotations",
        df=events_df,
        meanings=meanings,
    )

    print(f"\n✓ Successfully converted to EventsTable:")
    print(f"  - Number of events: {len(events_table)}")
    print(f"  - Columns: {list(events_table.columns.keys())}")

    return events_table


def save_sample_bids_files():
    """Save sample BIDS files to demonstrate file-based workflow"""
    print("\nSaving sample BIDS files for file-based conversion...")

    events_df, events_sidecar = create_sample_bids_data()

    # Create temporary files
    with tempfile.NamedTemporaryFile(mode="w", suffix="_events.tsv", delete=False) as events_file:
        events_df.to_csv(events_file.name, sep="\t", index=False)
        events_filename = events_file.name

    sidecar_filename = events_filename.replace("_events.tsv", "_events.json")
    with open(sidecar_filename, "w") as sidecar_file:
        json.dump(events_sidecar, sidecar_file, indent=2)

    print(f"  - Events file: {events_filename}")
    print(f"  - Sidecar file: {sidecar_filename}")

    return events_filename, sidecar_filename


def demonstrate_file_conversion():
    """Demonstrate conversion from actual BIDS files"""
    print("\nDemonstrating file-based BIDS conversion...")

    # Save sample files
    events_filename, sidecar_filename = save_sample_bids_files()

    try:
        # Load BIDS events data from files
        events_df = pd.read_csv(events_filename, sep="\t")
        with open(sidecar_filename, "r") as f:
            events_sidecar = json.load(f)

        print("Loaded BIDS data from files")

        # Extract meanings and convert
        meanings = extract_meanings(events_sidecar)
        events_table = get_events_table(
            name="file_based_events", description="Events loaded from BIDS files", df=events_df, meanings=meanings
        )

        print(f"✓ File-based conversion successful: {len(events_table)} events")

        return events_table

    finally:
        # Clean up temporary files
        for filename in [events_filename, sidecar_filename]:
            if os.path.exists(filename):
                os.remove(filename)
        print("Cleaned up temporary files")


def main():
    # Create NWB file with HED metadata
    nwbfile = NWBFile(
        session_description="BIDS to NWB conversion example",
        identifier="bids_conversion_example",
        session_start_time=datetime.now(),
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
    nwbfile.add_lab_meta_data(hed_metadata)

    # Demonstrate different conversion approaches
    events_table1 = demonstrate_bids_conversion()
    events_table2 = demonstrate_file_conversion()

    # Add EventsTables to NWB file
    nwbfile.add_acquisition(events_table1)
    nwbfile.add_acquisition(events_table2)

    print(f"\n✓ Successfully created NWB file with BIDS-converted events!")
    print(f"  - Memory-based conversion: {len(events_table1)} events")
    print(f"  - File-based conversion: {len(events_table2)} events")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
