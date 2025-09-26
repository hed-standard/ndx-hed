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

from ndx_events import EventsTable, NdxEventsNWBFile, DurationVectorData, CategoricalVectorData, MeaningsTable
from ndx_hed import HedTags, HedValueVector, HedLabMetaData
from datetime import datetime, timezone


def create_direct_hed_events():
    """Example 1: Direct HED annotations for each event"""
    print("1. Creating EventsTable with direct HED annotations...")

    events_table = EventsTable(name="stimulus_events", description="Stimulus events with direct HED annotations")

    # Add duration column first
    events_table.add_column(
        name="duration", 
        description="Event durations",
        data=[],  # Start empty, we'll add rows
        col_cls=DurationVectorData
    )

    # Add HED tags column for event-specific annotations
    events_table.add_column(
        name="HED",
        description="HED annotations for each event",
        data=[],  # Start empty, we'll add rows
        col_cls=HedTags
    )

    # Add rows of data
    events = [
        {"timestamp": 1.0, "duration": 0.5, "HED": "Eye-blink-artifact"},
        {"timestamp": 25.5, "duration": 3.5, "HED": "Chewing-artifact"},
        {"timestamp": 100.0, "duration": 1.05, "HED": "Movement-artifact"},
        {"timestamp": 200.5, "duration": 0.5, "HED": "Eye-movement-artifact"},
    ]
    
    for event in events:
        events_table.add_row(event)

    print(f"   Created table with {len(events_table)} events")
    return events_table


def create_value_vector_events():
    """Example 2: HedValueVector columns for shared annotations"""
    print("\n2. Creating EventsTable with HedValueVector columns...")

    events_table = EventsTable(name="behavioral_events", description="Events with HedValueVector columns")

    # Add intensity column with HED value annotation
    events_table.add_column(
        name="intensity",
        description="Brightness of visual stimulus",
        data=[],  # Start empty
        col_cls=HedValueVector,
        hed="(Luminance, Parameter-value/#)"
    )

    # Add reaction time column with HED annotation
    events_table.add_column(
        name="reaction_time",
        description="Participant response time",
        data=[],  # Start empty
        col_cls=HedValueVector,
        hed="(Behavioral-evidence, Parameter-label/Reaction-time, Time-interval/# s)"
    )

    # Add rows of data
    events = [
        {"timestamp": 1.0, "intensity": 0.3, "reaction_time": 0.45},
        {"timestamp": 2.5, "intensity": 0.7, "reaction_time": 0.52},
        {"timestamp": 4.0, "intensity": 0.5, "reaction_time": 0.38},
        {"timestamp": 5.5, "intensity": 0.9, "reaction_time": 0.61},
    ]
    
    for event in events:
        events_table.add_row(event)

    print(f"   Created table with {len(events_table)} events and HedValueVector columns")
    return events_table


def create_categorical_events():
    """Example 3: Categorical columns with HED in MeaningsTable"""
    print("\n3. Creating EventsTable with categorical columns and MeaningsTable...")

    events_table = EventsTable(name="categorized_events", description="Events with categorical data and MeaningsTable")

    # Create MeaningsTable with HED annotations
    stimulus_meanings = MeaningsTable(
        name="stimulus_type_meanings", description="Meanings and HED annotations for stimulus types"
    )

    # Add meaning definitions
    categories = [
        ("circle", "Circular visual stimulus presented at screen center"),
        ("square", "Square visual stimulus presented at screen center"),
        ("triangle", "Triangular visual stimulus presented at screen center"),
    ]

    for value, meaning in categories:
        stimulus_meanings.add_row(value=value, meaning=meaning)

    # Add HED annotations as a column in the MeaningsTable
    stimulus_meanings.add_column(
        name="HED",
        description="HED tags for stimulus categories",
        data=[
            "Sensory-event, Visual-presentation, Circle",
            "Sensory-event, Visual-presentation, Square",
            "Sensory-event, Visual-presentation, Triangle",
        ],
        col_cls=HedTags
    )

    # Add categorical column that references the meanings table
    events_table.add_column(
        name="stimulus_type",
        description="Type of visual stimulus presented",
        data=[],  # Start empty
        col_cls=CategoricalVectorData,
        meanings=stimulus_meanings
    )

    # Add rows of data
    events = [
        {"timestamp": 1.0, "stimulus_type": "circle"},
        {"timestamp": 2.0, "stimulus_type": "square"},
        {"timestamp": 3.0, "stimulus_type": "triangle"},
        {"timestamp": 4.0, "stimulus_type": "circle"},
    ]
    
    for event in events:
        events_table.add_row(event)

    print(
        f"   Created table with {len(events_table)} events and MeaningsTable with {len(stimulus_meanings)} categories"
    )
    return events_table


def main():
    # Create NWB file with HED metadata
    nwbfile = NdxEventsNWBFile(
        session_description="EventsTable HED integration examples",
        identifier="events_hed_example",
        session_start_time=datetime.now(timezone.utc),
    )

    # Add HED schema metadata
    hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
    nwbfile.add_lab_meta_data(hed_metadata)

    # Create the three types of EventsTable examples
    direct_events = create_direct_hed_events()
    value_vector_events = create_value_vector_events()
    categorical_events = create_categorical_events()

    # Add all tables to NWB file
    nwbfile.add_events_table(direct_events)
    nwbfile.add_events_table(value_vector_events)
    nwbfile.add_events_table(categorical_events)

    print(f"\n✓ Successfully created NWB file with EventsTable HED integration!")
    print(f"  - Direct HED events: {len(direct_events)} events")
    print(f"  - HedValueVector events: {len(value_vector_events)} events")
    print(f"  - Categorical events: {len(categorical_events)} events")

    return nwbfile


if __name__ == "__main__":
    nwbfile = main()
