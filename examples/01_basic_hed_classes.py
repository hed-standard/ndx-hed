#!/usr/bin/env python3
"""
Basic HED Classes Example
========================

This example demonstrates the three main classes provided by the ndx-hed extension:
1. HedLabMetaData - for HED schema specification
2. HedTags - for row-specific HED annotations
3. HedValueVector - for column-wide HED annotations with value placeholders

"""

from pynwb import NWBFile
from pynwb.core import DynamicTable, VectorData
from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from datetime import datetime, timezone


def main():
    # Create NWB file
    nwbfile = NWBFile(
        session_description="Basic HED classes demonstration",
        identifier="basic_hed_example",
        session_start_time=datetime.now(timezone.utc),
    )

    # 1. HedLabMetaData - Required for HED schema specification
    print("1. Creating HED Lab Metadata...")
    hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")  # Must be "hed_schema" if given
    nwbfile.add_lab_meta_data(hed_metadata)
    print(f"   Added HED schema version: {hed_metadata.hed_schema_version}")

    # 2. HedTags - For row-specific HED annotations
    print("\n2. Creating HedTags column...")
    hed_tags = HedTags(
        data=[
            "(Visual-presentation, Image, Building/House)",
            "(Auditory-presentation, Buzz)",
            "(Visual-presentation, Blue Square)",
        ]
    )

    # Create a dynamic table with HED annotations
    stim_table1 = DynamicTable(
        name="stimuli_information",
        description="Information about stimuli with HED annotations",
        columns=[
            VectorData(
                name="stim_type", description="Type of stimulus", data=["house-image", "buzz-sound", "blue-square"]
            ),
            hed_tags,  # Column name will automatically be "HED"
        ],
    )

    # Add rows with HED annotations
    stim_table1.add_row(stim_type="door-image", HED="(Visual-presentation, image, Building-part/Door)")
    print(f"   Created table with {len(stim_table1)} rows")
    print(f"   HED column name: {hed_tags.name}")

    # 3. HedValueVector - For column-wide annotations with value placeholders
    print("\n3. Creating HedValueVector column...")
    stimulus_column = HedValueVector(
        name="stimulus_intensity",
        description="Luminance contrast of visual stimuli against background",
        data=[0.5, 0.7, 0.3, 0.9],
        hed="Sensory-event, Visual-presentation, Luminance-contrast/#",
    )

    # Create another table with HedValueVector
    stim_table2 = DynamicTable(
        name="stimulus_data",
        description="Stimulus intensity with HED value annotations",
        columns=[VectorData(name="trial_number", description="Trial number", data=[1, 2, 3, 4]), stimulus_column],
    )
    print(f"   Created stimulus table with HED annotation: {stimulus_column.hed}")

    # Add tables to NWB file
    nwbfile.add_acquisition(stim_table1)
    nwbfile.add_acquisition(stim_table2)

    print("\n✓ Successfully created NWB file with HED annotations!")
    print(f"  - Stimulus table 1: {len(stim_table1)} rows")
    print(f"  - Stimulus table 2: {len(stim_table2)} rows")
    print(f"  - HED schema version: {hed_metadata.hed_schema_version}")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
