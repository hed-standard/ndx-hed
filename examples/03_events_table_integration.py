#!/usr/bin/env python3
"""
EventsTable Integration Example
===============================

This example demonstrates the three ways to integrate HED annotations with 
the ndx-events EventsTable:
1. Direct HED column for event-specific annotations
2. HedValueVector columns for shared annotations with value placeholders
3. Categorical columns with HED in MeaningsTable

"""

from pynwb import NWBFile
from ndx_events import EventsTable, TimestampVectorData, DurationVectorData, CategoricalVectorData, MeaningsTable
from ndx_hed import HedTags, HedValueVector, HedLabMetaData
from datetime import datetime

def create_direct_hed_events():
    """Example 1: Direct HED annotations for each event"""
    print("1. Creating EventsTable with direct HED annotations...")
    
    events_table = EventsTable(
        name="stimulus_events",
        description="Stimulus events with direct HED annotations"
    )

    # Add standard event columns
    events_table.add_column("timestamp", TimestampVectorData(
        name="timestamp",
        description="Event timestamps",
        data=[1.0, 25.5, 100.0, 200.5]
    ))

    events_table.add_column("duration", DurationVectorData(
        name="duration", 
        description="Event durations",
        data=[0.5, 3.5, 1.05, 0.5]
    ))

    # Add HED tags column for event-specific annotations
    events_table.add_column("HED", HedTags(
        name="HED",
        description="HED annotations for each event",
        data=["Eye-blink-artifact", 
              "Chewing-artifact", 
              "Movement-artifact",
              "Eye-movement-artifact"]
    ))

    print(f"   Created table with {len(events_table)} events")
    return events_table

def create_value_vector_events():
    """Example 2: HedValueVector columns for shared annotations"""
    print("\n2. Creating EventsTable with HedValueVector columns...")
    
    events_table = EventsTable(
        name="behavioral_events",
        description="Events with HedValueVector columns"
    )

    # Add timing columns
    events_table.add_column("timestamp", TimestampVectorData(
        name="timestamp",
        description="Event timestamps", 
        data=[1.0, 2.5, 4.0, 5.5]
    ))

    # Add intensity column with HED value annotation
    events_table.add_column("intensity", HedValueVector(
        name="stimulus_intensity",
        description="Brightness of visual stimulus",
        data=[0.3, 0.7, 0.5, 0.9],
        hed="(Luminance, Parameter-value/#)"
    ))

    # Add reaction time column with HED annotation
    events_table.add_column("reaction_time", HedValueVector(
        name="reaction_time", 
        description="Participant response time",
        data=[0.45, 0.52, 0.38, 0.61],
        hed="(Behavioral-evidence, Parameter-label/Reaction-time, Time-interval/# s)"
    ))

    print(f"   Created table with {len(events_table)} events and HedValueVector columns")
    return events_table

def create_categorical_events():
    """Example 3: Categorical columns with HED in MeaningsTable"""
    print("\n3. Creating EventsTable with categorical columns and MeaningsTable...")
    
    events_table = EventsTable(
        name="categorized_events",
        description="Events with categorical data and MeaningsTable"
    )

    # Add timing columns
    events_table.add_column("timestamp", TimestampVectorData(
        name="timestamp",
        description="Event timestamps",
        data=[1.0, 2.0, 3.0, 4.0]
    ))

    # Create MeaningsTable with HED annotations
    stimulus_meanings = MeaningsTable(
        name="stimulus_type_meanings",
        description="Meanings and HED annotations for stimulus types"
    )

    # Add meaning definitions
    categories = [
        ("circle", "Circular visual stimulus presented at screen center"),
        ("square", "Square visual stimulus presented at screen center"), 
        ("triangle", "Triangular visual stimulus presented at screen center")
    ]

    for value, meaning in categories:
        stimulus_meanings.add_row(value=value, meaning=meaning)

    # Add HED annotations as a column in the MeaningsTable
    stimulus_meanings.add_column("HED", HedTags(
        name="HED",
        description="HED tags for stimulus categories",
        data=[
            "Sensory-event, Visual-presentation, Circle",
            "Sensory-event, Visual-presentation, Square",
            "Sensory-event, Visual-presentation, Triangle"
        ]
    ))

    # Add the MeaningsTable to the EventsTable
    events_table.add_meanings_table(stimulus_meanings)

    # Add categorical column that references the meanings table
    events_table.add_column("stimulus_type", CategoricalVectorData(
        name="stimulus_type",
        description="Type of visual stimulus presented",
        data=["circle", "square", "triangle", "circle"],
        meanings=stimulus_meanings
    ))

    print(f"   Created table with {len(events_table)} events and MeaningsTable with {len(stimulus_meanings)} categories")
    return events_table

def main():
    # Create NWB file with HED metadata
    nwbfile = NWBFile(
        session_description="EventsTable HED integration examples",
        identifier="events_hed_example",
        session_start_time=datetime.now()
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
    nwbfile.add_lab_meta_data(hed_metadata)

    # Create the three types of EventsTable examples
    direct_events = create_direct_hed_events()
    value_vector_events = create_value_vector_events()
    categorical_events = create_categorical_events()

    # Add all tables to NWB file
    nwbfile.add_acquisition(direct_events)
    nwbfile.add_acquisition(value_vector_events)
    nwbfile.add_acquisition(categorical_events)

    print(f"\n✓ Successfully created NWB file with EventsTable HED integration!")
    print(f"  - Direct HED events: {len(direct_events)} events")
    print(f"  - HedValueVector events: {len(value_vector_events)} events")
    print(f"  - Categorical events: {len(categorical_events)} events")

    return nwbfile

if __name__ == "__main__":
    nwbfile = main()
