#!/usr/bin/env python3
"""
Working with Trials Example
===========================

This example demonstrates how to add HED annotations to the trials table in NWB.

"""

from pynwb import NWBFile
from ndx_hed import HedTags, HedLabMetaData
from datetime import datetime


def main():
    # Create NWB file with HED metadata
    nwbfile = NWBFile(
        session_description="Example session with HED annotations in trials",
        identifier="trials_hed_example",
        session_start_time=datetime.now(),
    )

    # Add HED schema metadata
    print("Setting up HED metadata...")
    hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
    nwbfile.add_lab_meta_data(hed_metadata)

    # Add HED column to trials table
    print("Adding HED column to trials table...")
    nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")

    # Add trials with HED annotations
    print("Adding trials with HED annotations...")

    # Trial 1: Visual stimulus presentation
    nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Experimental-trial, (Sensory-event, Visual-presentation)")

    # Trial 2: Participant response
    nwbfile.add_trial(
        start_time=2.0, stop_time=3.0, HED="Experimental-trial, (Agent-action, Participant-response, Button-press)"
    )

    # Trial 3: Auditory stimulus
    nwbfile.add_trial(
        start_time=4.0, stop_time=5.0, HED="Experimental-trial, (Sensory-event, Auditory-presentation, Tone)"
    )

    # Trial 4: Rest period
    nwbfile.add_trial(start_time=6.0, stop_time=8.0, HED="Experimental-trial, Rest")

    print(f"\n✓ Successfully created trials table with HED annotations!")
    print(f"  - Number of trials: {len(nwbfile.trials)}")
    print(f"  - Trial columns: {list(nwbfile.trials.colnames)}")

    # Display trial information
    print("\nTrial details:")
    for i, trial in enumerate(nwbfile.trials.to_dataframe().iterrows()):
        idx, row = trial
        print(f"  Trial {i+1}: {row['start_time']:.1f}-{row['stop_time']:.1f}s, " f"HED: {row['HED']}")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
