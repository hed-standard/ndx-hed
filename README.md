[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13142816.svg)](https://doi.org/10.5281/zenodo.13142816)
[![PyPI version](https://badge.fury.io/py/ndx-hed.svg)](https://badge.fury.io/py/ndx-hed)

# ndx-hed Extension for NWB

[**Neurodata Without Borders (NWB)**](https://www.nwb.org/) is a data standard for organizing neurophysiology data.
NWB is used extensively as the data representation for single cell and animal recordings as well as
human neuroimaging modalities such as IEEG. HED (Hierarchical Event Descriptors) is a system of
standardized vocabularies and supporting tools that allows fine-grained annotation of data.
HED annotations can now be used in NWB to provide a column of HED annotations for any NWB
dynamic table. 

The [**HED annotation in NWB**](https://www.hed-resources.org/en/latest/HedAnnotationInNWB.html)
user guide explains in more detail how to use this extension for HED.

## Installation

**Python:**
```bash
pip install -U ndx-hed
```

**Matlab:**  The Matlab extension is under development.

## Main Classes

The ndx-hed extension provides three main classes for working with HED annotations in NWB:

### 1. HedLabMetaData

A `NWBFile` can be associated with only one HED schema version specification.
If you are using HED for your NWB data, you should always create a `HedLabMetadata` object with that version and use it for all validation of
all elements of your dataset. Internally, the `HedLabMetadata` creates and caches the HED schema object needed for validation.

```python
from ndx_hed import HedLabMetaData

# Create HED metadata with schema version
hed_metadata = HedLabMetaData(
    name="hed_schema",  # Must be "hed_schema" if given
    hed_schema_version="8.4.0"
)

# Add to NWB file
nwbfile.add_lab_meta_data(hed_metadata)
```

### 2. HedTags

A specialized `VectorData` column for storing HED tag strings. This class is used for adding HED annotations to any NWB dynamic table. 
Each row contains a string representing the HED annotation for that row in the table.

```python
from ndx_hed import HedTags
from pynwb.core import DynamicTable, VectorData

# Create HedTags column
hed_tags = HedTags(data=[
    "Sensory-event, Visual-presentation",
    "Agent-action, Participant-response",
    "Experimental-trial"
])

# Add to a dynamic table
my_table = DynamicTable(
    name='events',
    description='Event data with HED annotations',
    columns=[
        VectorData(name="event_type", description="Type of event", data=["stimulus", "response", "trial"]),
        hed_tags  # Column name will automatically be "HED"
    ]
)

# Add rows with HED annotations
my_table.add_row(event_type="button_press", HED="Agent-action, Press")
```

### 3. HedValueVector

A `VectorData` column where all values share the same HED annotation. Useful for columns where the HED tag applies to each element in the entire column rather than individual rows. The HED

```python
from ndx_hed import HedValueVector

# Create a column where all values have the same HED annotation
stimulus_column = HedValueVector(
    name="stimulus_intensity",
    description="Intensity of visual stimulus",
    data=[0.5, 0.7, 0.3, 0.9],
    hed="Sensory-event, Visual-presentation, Luminance-attribute/#"
)
```
### HED integration in NWB

| Class | Use cases |
| ----- | ----------|
| `HedTags` | <ul><li>Can be added to any `DynamicTable`</li><li>Annotation applies to each row</li><li>When added to a `MeaningsTable`, annotates a category.</li></ul> |
| `HedValueVector` | <ul><li>Can be added to any `DynamicTable`</li><li>Gives a single HED annotation template values in a column.</li></ul> |

Using `HedTags` and `HedValueVector` in combination provides a flexible way of integrating HED annotations
into NWB.
This multi-level approach provides several advantages:

1. **Granular annotations**: Direct HED columns allow event-specific details
2. **Efficient reuse**: `HedValueVector` avoids repetition for column-wide annotations  
3. **Categorical organization**: `MeaningsTable` provides structured categorical metadata
4. **Validation**: All HED annotations can be validated using the `HedNWBValidator`
5. **BIDS compatibility**: Supports conversion between NWB events and [BIDS (Brain Imaging Data Structure)]([https://](https://bids.neuroimaging.io/index.html)events and their annotations

## Working with trials

A common use case is adding HED annotations to the trials table:

```python
from pynwb import NWBFile
from ndx_hed import HedTags, HedLabMetaData
from datetime import datetime

# Create NWB file with HED metadata
nwbfile = NWBFile(
    session_description="Example session with HED annotations",
    identifier="example_session_001",
    session_start_time=datetime.now()
)

# Add HED schema metadata
hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
nwbfile.add_lab_meta_data(hed_metadata)

# Add HED column to trials table
nwbfile.add_trial_column(
    name="HED",
    col_cls=HedTags,
    data=[],
    description="HED annotations for trials"
)

# Add trials with HED annotations
nwbfile.add_trial(
    start_time=0.0,
    stop_time=1.0,
    HED="Experimental-trial, (Sensory-event, Visual-presentation)"
)

nwbfile.add_trial(
    start_time=2.0,
    stop_time=3.0,
    HED="Experimental-trial, (Agent-action, Participant-response, Button-press)"
)
```

## Integration with NWB events 

The ndx-hed extension works seamlessly with the [ndx-events extension](https://github.com/rly/ndx-events) to provide comprehensive event annotation capabilities. The ndx-events extension introduces standardized data types for storing timestamped event data, and HED annotations can be incorporated in three different ways within the `EventsTable` and `MeaningsTable` structures.

### Overview of ndx-events extension

The ndx-events extension provides:
- **EventsTable**: A specialized table for storing timestamped events with metadata
- **MeaningsTable**: A table that maps categorical values to their detailed descriptions
- **CategoricalVectorData**: Columns that reference a `MeaningsTable` for value definitions
- **TimestampVectorData**: Starting time of the event represented by that row (must be called `time_stamp`)
- **DurationVectorData**: Durationof the event represented by that row (must be called `duration`)

There can be multiple `EventsTable` type tables in a single `NWBFile`, stored under `events`. The `nwbfile.get_allEvents()` merges these tables into a single read-only table sorted by timestamp.

### Three ways to add HED to EventsTable

#### 1. Direct addition of a HED column

Add a `HedTags` column directly to an `EventsTable` for event-specific HED annotations:

```python
from ndx_events import EventsTable, TimestampVectorData, DurationVectorData
from ndx_hed import HedTags, HedLabMetaData
import numpy as np

# Create EventsTable with HED annotations
events_table = EventsTable(
    name="stimulus_events",
    description="Subject induced artifacts in the signal"
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

# Add HED tags column
events_table.add_column("HED", HedTags(
    name="HED",
    description="HED annotations for each event",
    data=["Eye-blink-artifact", 
          "Chewing-artifact", 
          "Movement-artifact",
          "Eye-movement-artifact"]
))
```

As illustrated by the example, the HED tag column is best
for annotations that are specific to each event, such as
for annotations of artifacts, subject behavior, or external events.

Events that share annotations or whose annotations fall into categories are better represented by `HedValueVector` columns or
`CategoricalVectorData` with meanings, respectively.

#### 2. HedValueVector Columns in EventsTable

Use `HedValueVector` for columns where all values share the same HED annotation but differ by particular value.  
HED value annotations use a `#` as a placeholder where that value
is to be substituted for in the annotation by that particular value.
For example, if a column represents the speed of a mouse moving through a maze, a HED annotation `"Speed/# cm/s"` could be applicable to all the values in that column.  

```python
from ndx_hed import HedValueVector

# Add a column where all stimulus intensities have the same HED context
events_table = EventsTable(
    name="stimulus_events",
    description="Stimulus events"
)
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
    hed="(Behavioral-evidence, Parameter-label/Reaction-time,Time-interval/# s)"
))
```

#### 3. Categorical columns and MeaningsTable

In many experiments, events that represent the task (e.g., repeated stimuli) fall into a limited number of categories and
each category can be annotated with HED. 
Use columns of type `CategoricalVectorData` for the categorical data with HED annotations stored in a corresponding `MeaningsTable`:

```python
from ndx_events import CategoricalVectorData, MeaningsTable

# Create MeaningsTable with HED annotations
stimulus_meanings = MeaningsTable(
    name="stimulus_type_meanings",
    description="Meanings and HED annotations for stimulus types"
)

# Add the standard meaning columns
stimulus_meanings.add_row(
    value="circle",
    meaning="Circular visual stimulus presented at screen center"
)
stimulus_meanings.add_row(
    value="square", 
    meaning="Square visual stimulus presented at screen center"
)
stimulus_meanings.add_row(
    value="triangle",
    meaning="Triangular visual stimulus presented at screen center"
)

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
```

### Complete example with All HED types

```python
from pynwb import NWBFile
from ndx_events import EventsTable, TimestampVectorData, DurationVectorData, CategoricalVectorData, MeaningsTable
from ndx_hed import HedTags, HedValueVector, HedLabMetaData
from datetime import datetime

# Create NWB file with HED metadata
nwbfile = NWBFile(
    session_description="Experiment with comprehensive HED annotations in EventsTable",
    identifier="hed_events_example",
    session_start_time=datetime.now()
)

# Add HED schema metadata
hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
nwbfile.add_lab_meta_data(hed_metadata)

# Create comprehensive EventsTable
events_table = EventsTable(
    name="comprehensive_events",
    description="Events with multiple types of HED annotations"
)

# 1. Standard event timing columns
events_table.add_column("timestamp", TimestampVectorData(
    name="timestamp",
    description="Event onset times",
    data=[1.0, 2.5, 4.0, 5.5, 7.0]
))

events_table.add_column("duration", DurationVectorData(
    name="duration",
    description="Event durations", 
    data=[0.5, 0.3, 0.8, 0.4, 0.6]
))

# 2. Direct HED annotations for each event
events_table.add_column("HED", HedTags(
    name="HED",
    description="Event-specific HED annotations",
    data=[
        "Experimental-trial, (Sensory-event, Visual-presentation)",
        "Experimental-trial, (Agent-action, Participant-response)",
        "Experimental-trial, (Sensory-event, Auditory-presentation)", 
        "Experimental-trial, (Agent-action, Participant-response)",
        "Experimental-trial, Pause"
    ]
))

# 3. HedValueVector columns
events_table.add_column("stimulus_intensity", HedValueVector(
    name="stimulus_intensity",
    description="Stimulus intensity values",
    data=[0.7, 0.0, 0.9, 0.0, 0.0],  # 0.0 for non-stimulus events
    hed="Sensory-event, Luminance-attribute/#"
))

# 4. Categorical column with HED in MeaningsTable
event_meanings = MeaningsTable(
    name="event_type_meanings",
    description="Event type categories with HED annotations"
)

# Define event categories
categories = [
    ("visual_stim", "Visual stimulus presentation", "Sensory-event, Visual-presentation"),
    ("button_press", "Participant button press response", "Agent-action, Participant-response, Button-press"),
    ("audio_stim", "Auditory stimulus presentation", "Sensory-event, Auditory-presentation"),
    ("pause", "Inter-trial pause period", "Pause")
]

for value, meaning, hed_tag in categories:
    event_meanings.add_row(value=value, meaning=meaning)

# Add HED column to meanings table
event_meanings.add_column("HED", HedTags(
    name="HED", 
    description="HED annotations for event categories",
    data=[cat[2] for cat in categories]
))

# Add meanings table and categorical column
events_table.add_meanings_table(event_meanings)
events_table.add_column("event_type", CategoricalVectorData(
    name="event_type",
    description="Categorical event type",
    data=["visual_stim", "button_press", "audio_stim", "button_press", "pause"],
    meanings=event_meanings
))

# Add to NWB file
nwbfile.add_events_table(events_table)
```


## BIDS to NWB conversion
[BIDS (Brain Imaging Data Structure)](https://bids.neuroimaging.io/index.html) is a standard for
representing neuroimaging/behavioral experiments in a standardized format.
The ndx-hed extension provides utilities to convert BIDS events files with sidecars and HED annotations to/from the
equivalent NWB `EventsTable` format.
Further, validating an `EventsTable` consists of converting
the `EventsTable` to its equivalent BIDS event table and JSON sidecar, validating the result, and translating any resulting
issues into appropriate NWB issues.

### Converting BIDS events to EventsTable

```python
import pandas as pd
import json
from ndx_hed.utils.bids2nwb import extract_meanings, get_events_table

# Load BIDS events data
events_df = pd.read_csv("events.tsv", sep="\t")
with open("events.json", "r") as f:
    events_sidecar = json.load(f)

# Extract meanings from sidecar JSON
meanings = extract_meanings(events_sidecar)

# Convert to EventsTable
events_table = get_events_table(
    name="task_events",
    description="Task events with HED annotations",
    df=events_df,
    meanings=meanings
)

# Add to NWB file
nwbfile.add_acquisition(events_table)
```

### Example BIDS Sidecar Structure

```json
{
    "event_type": {
        "Levels": {
            "stimulus": "Visual stimulus presentation",
            "response": "Participant button press"
        },
        "HED": {
            "stimulus": "Sensory-event, Visual-presentation",
            "response": "Agent-action, Participant-response, Button-press"
        }
    },
    "trial_number": {
        "Description": "Trial number in the experiment",
        "HED": "Experimental-trial/#"
    }
}
```

## HED Validation

The extension provides validation capabilities to ensure HED annotations conform to the specified schema:

### Validating HED Tags in Tables

```python
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from hed.errors import ErrorHandler

# Create validator with HED metadata
validator = HedNWBValidator(hed_metadata)

# Validate a table with HED annotations
error_handler = ErrorHandler()
issues = validator.validate_table(my_table, error_handler)

if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All HED annotations are valid!")
```

### Validating Individual HedTags Columns

```python
# Validate a specific HedTags column
hed_column = my_table["HED"]
issues = validator.validate_vector(hed_column)

if not issues:
    print("HED column is valid!")
```

### Validating EventsTable

```python
# Validate HED annotations in an EventsTable
issues = validator.validate_events(events_table)

if issues:
    print("EventsTable validation issues:")
    for issue in issues:
        print(f"  - Row {issue.get('row', 'unknown')}: {issue}")
```

## Complete Example

Here's a complete example showing the main workflow:

```python
from pynwb import NWBFile, NWBHDF5IO
from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from pynwb.core import DynamicTable, VectorData
from datetime import datetime
import pandas as pd

# 1. Create NWB file with HED metadata
nwbfile = NWBFile(
    session_description="Example experiment with HED annotations",
    identifier="exp_001",
    session_start_time=datetime.now()
)

# 2. Add HED schema metadata
hed_metadata = HedLabMetaData(hed_schema_version="8.3.0")
nwbfile.add_lab_meta_data(hed_metadata)

# 3. Create a custom events table with HED annotations
events_table = DynamicTable(
    name="behavioral_events",
    description="Behavioral events during the experiment",
    columns=[
        VectorData(name="event_time", description="Time of event", data=[1.5, 3.2, 5.8, 7.1]),
        VectorData(name="event_type", description="Type of event", data=["stimulus", "response", "stimulus", "response"]),
        HedTags(data=[
            "Sensory-event, Visual-presentation, (Red, Circle)",
            "Agent-action, Participant-response, Button-press",
            "Sensory-event, Visual-presentation, (Blue, Square)", 
            "Agent-action, Participant-response, Button-press"
        ]),
        HedValueVector(
            name="reaction_time",
            description="Reaction time in seconds",
            data=[None, 0.5, None, 0.3],
            hed="Behavioral-evidence, Reaction-time/#"
        )
    ]
)

# 4. Add table to NWB file
nwbfile.add_acquisition(events_table)

# 5. Validate HED annotations
validator = HedNWBValidator(hed_metadata)
issues = validator.validate_table(events_table)

if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All HED annotations are valid!")

# 6. Save NWB file
with NWBHDF5IO("example_with_hed.nwb", "w") as io:
    io.write(nwbfile)

print("NWB file with HED annotations saved successfully!")
```

## Additional Resources

- [HED Specification](https://www.hedtags.org/)
- [HED Python Tools](https://github.com/hed-standard/hed-python)
- [HED annotation in NWB User Guide](https://www.hed-resources.org/en/latest/HedAnnotationInNWB.html)
- [NWB Documentation](https://pynwb.readthedocs.io/)

## Contributing

Contributions are welcome! Please see the [contributing guidelines](NEXTSTEPS.md) and feel free to submit issues or pull requests.
