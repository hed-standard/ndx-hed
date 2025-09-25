#!/usr/bin/env python3
"""
Advanced Integration Example
============================

This example demonstrates advanced real-world usage patterns with ndx-hed:
1. Complex experimental design with multiple event types
2. Integration with multiple NWB data types
3. Advanced validation and error handling
4. Performance considerations with large datasets

"""

import numpy as np
import pandas as pd
from pynwb import NWBFile, TimeSeries
from pynwb.core import DynamicTable, VectorData
from pynwb.behavior import Position, SpatialSeries
from pynwb.ophys import ImageSeries
from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from ndx_events import EventsTable, TimestampVectorData, DurationVectorData
from hed.errors import ErrorHandler
from datetime import datetime


def create_complex_experimental_session():
    """Create a complex NWB file representing a real experimental session"""
    print("1. Creating complex experimental session...")
    
    # Create NWB file for a visual attention task with eye tracking
    nwbfile = NWBFile(
        session_description="Visual attention task with eye tracking and neural recordings",
        identifier="complex_session_001", 
        session_start_time=datetime.now(),
        experimenter=["Dr. Smith", "Dr. Johnson"],
        lab="Attention & Perception Lab",
        institution="Research University",
        session_id="sess001_subj05",
        subject=None  # Would normally include subject metadata
    )
    
    # Add comprehensive HED metadata with experimental definitions using valid HED tags
    # Note: These are simplified definitions for demonstration
    experimental_definitions = "(Definition/Fixation-cross, (Sensory-event, Visual-presentation)), (Definition/Target-stimulus, (Sensory-event, Visual-presentation)), (Definition/Distractor-stimulus, (Sensory-event, Visual-presentation)), (Definition/Correct-saccade, (Agent-action)), (Definition/Incorrect-saccade, (Agent-action))"
    
    hed_metadata = HedLabMetaData(
        hed_schema_version="8.3.0",
        definitions=experimental_definitions
    )
    nwbfile.add_lab_meta_data(hed_metadata)
    
    print(f"   - Session: {nwbfile.session_description}")
    print(f"   - Definitions: {len(hed_metadata.get_definition_dict().defs)}")
    
    return nwbfile, hed_metadata


def add_behavioral_data_with_hed(nwbfile):
    """Add behavioral data with comprehensive HED annotations"""
    print("\n2. Adding behavioral data with HED annotations...")
    
    # Simulate eye tracking data
    n_samples = 10000
    timestamps = np.linspace(0, 100, n_samples)  # 100 seconds at 100Hz
    
    # Eye position data (x, y coordinates)
    eye_x = np.random.normal(0, 50, n_samples) + 10 * np.sin(timestamps * 0.1)
    eye_y = np.random.normal(0, 30, n_samples) + 5 * np.cos(timestamps * 0.15)
    
    # Create spatial series for eye tracking
    eye_position = SpatialSeries(
        name="eye_position",
        description="Eye position coordinates during task",
        data=np.column_stack([eye_x, eye_y]),
        timestamps=timestamps,
        reference_frame="Screen coordinates (pixels from center)",
        unit="pixels"
    )
    
    # Add to behavior module
    behavior_module = nwbfile.create_processing_module(
        name="behavior", 
        description="Behavioral data and events"
    )
    
    position_container = Position(name="eye_tracking")
    position_container.add_spatial_series(eye_position)
    behavior_module.add(position_container)
    
    print(f"   - Added eye tracking data: {len(timestamps)} samples")
    return behavior_module


def create_detailed_trials_table(nwbfile):
    """Create detailed trials table with multiple HED annotation types"""
    print("\n3. Creating detailed trials table...")
    
    # Add multiple HED-annotated columns
    nwbfile.add_trial_column(
        name="HED", 
        col_cls=HedTags, 
        data=[], 
        description="Primary HED annotations"
    )
    
    nwbfile.add_trial_column(
        name="attention_level",
        col_cls=HedValueVector,
        data=[],
        description="Attention level rating",
        hed="Behavioral-evidence, Attention-level/#"
    )
    
    nwbfile.add_trial_column(
        name="difficulty",
        col_cls=HedValueVector, 
        data=[],
        description="Task difficulty level",
        hed="Task-property, Difficulty-level/#"
    )
    
    # Add additional trial metadata columns
    nwbfile.add_trial_column(
        name="trial_type",
        description="Type of trial (cue condition)",
        data=[]
    )
    
    nwbfile.add_trial_column(
        name="outcome", 
        description="Trial outcome",
        data=[]
    )
    
    # Generate realistic trial data
    n_trials = 120
    trial_types = ["valid_cue", "invalid_cue", "neutral_cue", "no_cue"] 
    outcomes = ["correct", "incorrect", "no_response"]
    
    for trial_num in range(n_trials):
        start_time = trial_num * 2.5  # 2.5 seconds per trial
        stop_time = start_time + 2.0
        
        trial_type = np.random.choice(trial_types)
        outcome = np.random.choice(outcomes, p=[0.7, 0.2, 0.1])  # Weighted probabilities
        attention_level = np.random.uniform(3, 9)  # 1-10 scale
        difficulty = np.random.choice([1, 2, 3, 4, 5])
        
        # Construct HED annotation based on trial parameters
        hed_parts = [f"Experimental-trial"]
        
        if trial_type == "valid_cue":
            hed_parts.append("Target-stimulus, (Valid, Cue)")
        elif trial_type == "invalid_cue": 
            hed_parts.append("Target-stimulus, (Invalid, Cue)")
        elif trial_type == "neutral_cue":
            hed_parts.append("Target-stimulus, (Neutral, Cue)")
        else:  # no_cue
            hed_parts.append("Target-stimulus")
        
        if outcome == "correct":
            reaction_time = np.random.uniform(250, 600)  # ms
            hed_parts.extend([
                "Correct-saccade"
            ])
        elif outcome == "incorrect":
            reaction_time = np.random.uniform(200, 800)  # ms 
            hed_parts.extend([
                "Incorrect-saccade"
            ])
        # no_response gets no additional annotations
        
        hed_annotation = ", ".join(hed_parts)
        
        nwbfile.add_trial(
            start_time=start_time,
            stop_time=stop_time,
            HED=hed_annotation,
            attention_level=attention_level,
            difficulty=difficulty,
            trial_type=trial_type,
            outcome=outcome
        )
    
    print(f"   - Added {n_trials} trials with detailed HED annotations")
    return n_trials


def create_stimulus_events_table(nwbfile):
    """Create simplified stimulus events table using DynamicTable"""
    print("\n4. Creating stimulus events table...")
    
    # Generate stimulus events that align with trials
    n_events = 200  # Reduced for simplicity
    
    # Event data
    event_times = sorted(np.random.uniform(0, 300, n_events))
    event_durations = np.random.uniform(0.05, 0.5, n_events)
    event_types = np.random.choice(
        ["fixation", "target", "distractor", "feedback"], 
        n_events,
        p=[0.3, 0.25, 0.25, 0.2]
    )
    
    # HED annotations for each event
    hed_annotations = []
    for event_type in event_types:
        if event_type == "fixation":
            hed_annotations.append("Fixation-cross")
        elif event_type == "target":
            hed_annotations.append("Target-stimulus")
        elif event_type == "distractor":
            hed_annotations.append("Distractor-stimulus")
        elif event_type == "feedback":
            hed_annotations.append("Sensory-event, Auditory-presentation")
    
    # Create DynamicTable instead of EventsTable for simplicity
    from pynwb.core import DynamicTable, VectorData
    
    stimulus_events = DynamicTable(
        name="stimulus_events",
        description="Detailed stimulus presentation events",
        columns=[
            VectorData(name="timestamp", description="Event onset times", data=event_times),
            VectorData(name="duration", description="Event durations", data=event_durations),
            VectorData(name="event_type", description="Type of event", data=event_types),
            HedTags(name="HED", description="HED annotations for stimulus events", data=hed_annotations),
            HedValueVector(
                name="luminance",
                description="Stimulus luminance values",
                data=np.random.uniform(0.1, 1.0, n_events),
                hed="Sensory-attribute, Luminance-attribute/#"
            )
        ]
    )
    
    nwbfile.add_acquisition(stimulus_events)
    print(f"   - Added {n_events} stimulus events")
    return stimulus_events


def perform_comprehensive_validation(hed_metadata, nwbfile):
    """Perform comprehensive validation with detailed error reporting"""
    print("\n5. Performing comprehensive validation...")
    
    # Create validator with custom error handler
    error_handler = ErrorHandler(check_for_warnings=True)
    validator = HedNWBValidator(hed_metadata)
    
    # Validate different components
    validation_results = {}
    
    # Validate trials table
    if nwbfile.trials is not None:
        trials_issues = validator.validate_table(nwbfile.trials, error_handler)
        validation_results["trials"] = trials_issues
        print(f"   - Trials table: {len(trials_issues)} issues")
    
    # Validate stimulus events (now a DynamicTable)
    stimulus_events = nwbfile.acquisition.get("stimulus_events")
    if stimulus_events:
        events_issues = validator.validate_table(stimulus_events, error_handler)
        validation_results["stimulus_events"] = events_issues
        print(f"   - Stimulus events: {len(events_issues)} issues")
    
    # Full file validation
    all_issues = validator.validate_file(nwbfile, error_handler)
    validation_results["full_file"] = all_issues
    
    print(f"   - Total file issues: {len(all_issues)}")
    
    # Report issue breakdown
    if all_issues:
        severity_counts = {}
        for issue in all_issues:
            severity = issue.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("   - Issue breakdown by severity:")
        for severity, count in severity_counts.items():
            print(f"     • {severity}: {count}")
    else:
        print("   ✓ All HED annotations are valid!")
    
    return validation_results


def demonstrate_performance_considerations(nwbfile):
    """Demonstrate performance considerations with large datasets"""
    print("\n6. Performance considerations...")
    
    # Show memory usage of HED annotations
    total_hed_strings = 0
    total_hed_length = 0
    
    # Count HED strings in trials
    if nwbfile.trials is not None:
        for col in nwbfile.trials.columns:
            if isinstance(col, HedTags):
                total_hed_strings += len(col.data)
                total_hed_length += sum(len(str(tag)) for tag in col.data)
    
    # Count HED strings in acquisition tables
    for acq_name, acq_obj in nwbfile.acquisition.items():
        if hasattr(acq_obj, 'columns'):
            for col in acq_obj.columns:
                if isinstance(col, HedTags):
                    total_hed_strings += len(col.data)
                    total_hed_length += sum(len(str(tag)) for tag in col.data)
    
    avg_hed_length = total_hed_length / total_hed_strings if total_hed_strings > 0 else 0
    
    print(f"   - Total HED annotation strings: {total_hed_strings}")
    print(f"   - Average HED string length: {avg_hed_length:.1f} characters")
    print(f"   - Total HED content: {total_hed_length / 1024:.1f} KB")
    
    # Recommendations
    print("\n   Performance recommendations:")
    print("   • Use HedValueVector for repeated patterns")
    print("   • Define custom definitions for complex, reused annotations")
    print("   • Validate incrementally during data creation")
    print("   • Consider HED string length vs. expressiveness trade-offs")


def generate_summary_report(nwbfile, hed_metadata, validation_results):
    """Generate comprehensive summary report"""
    print("\n" + "="*60)
    print("ADVANCED INTEGRATION SUMMARY REPORT")
    print("="*60)
    
    print(f"Session: {nwbfile.identifier}")
    print(f"Description: {nwbfile.session_description}")
    print(f"HED Schema: {hed_metadata.hed_schema_version}")
    print(f"Custom Definitions: {len(hed_metadata.get_definition_dict().defs)}")
    
    print("\nData Summary:")
    print(f"  • Trials: {len(nwbfile.trials) if nwbfile.trials else 0}")
    print(f"  • Acquisition objects: {len(nwbfile.acquisition)}")
    print(f"  • Processing modules: {len(nwbfile.processing)}")
    
    print("\nHED Annotation Summary:")
    for table_name, issues in validation_results.items():
        print(f"  • {table_name}: {len(issues)} validation issues")
    
    print("\nDefinitions Used:")
    for def_name, def_entry in hed_metadata.get_definition_dict().defs.items():
        takes_value = " (takes value)" if def_entry.takes_value else ""
        print(f"  • {def_name}{takes_value}")
    
    total_issues = sum(len(issues) for issues in validation_results.values())
    if total_issues == 0:
        print("\n✅ ALL HED ANNOTATIONS ARE VALID!")
    else:
        print(f"\n⚠️  Total validation issues: {total_issues}")


def main():
    # Create complex experimental session
    nwbfile, hed_metadata = create_complex_experimental_session()
    
    # Add various data types with HED annotations
    behavior_module = add_behavioral_data_with_hed(nwbfile)
    n_trials = create_detailed_trials_table(nwbfile)
    stimulus_events = create_stimulus_events_table(nwbfile)
    
    # Comprehensive validation
    validation_results = perform_comprehensive_validation(hed_metadata, nwbfile)
    
    # Performance analysis
    demonstrate_performance_considerations(nwbfile)
    
    # Final summary
    generate_summary_report(nwbfile, hed_metadata, validation_results)
    
    return nwbfile


if __name__ == "__main__":
    nwbfile = main()