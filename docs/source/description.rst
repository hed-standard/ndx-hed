Getting Started
===============

Overview
--------

The **ndx-hed** extension integrates HED (Hierarchical Event Descriptors) annotations into NWB (Neurodata Without Borders) neurophysiology data files. 

`Neurodata Without Borders (NWB) <https://www.nwb.org/>`_ is a data standard for organizing neurophysiology data.
NWB is used extensively as the data representation for single cell and animal recordings as well as
human neuroimaging modalities such as IEEG. NWB organizes all of the data from one recording session into a single file.

`HED (Hierarchical Event Descriptors) <https://www.hedtags.org>`_ is a system of
standardized vocabularies and supporting tools that allows fine-grained annotation of data.
HED annotations can now be used in NWB to provide HED annotations for any NWB dynamic table.

The `HED annotation in NWB user guide <https://www.hedtags.org/hed-resources/HedAnnotationInNWB.html>`_
explains in more detail how to use this extension for HED.

.. note::
   All examples referenced in this documentation can be found in the `examples directory <https://github.com/VisLab/ndx-hed/tree/main/examples>`_ 
   and can be run directly from the ``examples/`` folder.

Three Core Classes
------------------

The ndx-hed extension provides three main classes for different annotation patterns:

HedLabMetaData
~~~~~~~~~~~~~~

**Purpose**: Required metadata container for HED schema specification and lab-specific definitions.

**Key Features**:

* Stores HED schema version for the entire NWB file
* Supports both standard and library schemas  
* Manages custom HED definitions
* Must be added to ``NWBFile`` before using any HED annotations
* Must be named "hed_schema" (enforced by constructor)

**Use Cases**: Required for all HED validation and schema management.

.. code-block:: python

   from ndx_hed import HedLabMetaData
   
   # Basic schema specification
   hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
   nwbfile.add_lab_meta_data(hed_metadata)
   
   # With custom definitions
   definitions = "(Definition/Fixation-task, (Task, Fixate))"
   hed_metadata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)

HedTags
~~~~~~~

**Purpose**: Row-specific HED annotations extending NWB ``VectorData`` class.

**Key Features**:

* Stores one HED string per table row
* Must be named "HED" (enforced by constructor)
* Works with any NWB ``DynamicTable`` (trials, units, epochs, etc.)
* Ideal for event-specific annotations

**Use Cases**: Row-specific tags in any DynamicTable.

.. code-block:: python

   from ndx_hed import HedTags
   
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

HedValueVector
~~~~~~~~~~~~~~

**Purpose**: Column-wide HED templates with value placeholders.

**Key Features**:

* Stores numerical/categorical data with HED templates
* Uses ``#`` placeholder for values (e.g., "Duration/# s")
* HED annotation applies to entire column
* Ideal for parametric annotations

**Use Cases**: Shared annotations with value placeholders (#).

.. code-block:: python

   from ndx_hed import HedValueVector
   
   # Create template-based annotations
   duration_vector = HedValueVector(
       name="duration",
       description="Trial duration with HED annotation for a sensory stimulus",
       data=[1.0, 1.5, 2.0],
       hed="((Sensory-event, Experiment-stimulus), Duration/# s)"
   )
   
   trials_table.add_column(duration_vector)

Comprehensive Examples
----------------------

The `examples directory <https://github.com/VisLab/ndx-hed/tree/main/examples>`_ contains comprehensive runnable examples:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Example
     - Description
   * - `01_basic_hed_classes.py <https://github.com/VisLab/ndx-hed/blob/main/examples/01_basic_hed_classes.py>`_
     - Introduction to the three main classes
   * - `02_trials_with_hed.py <https://github.com/VisLab/ndx-hed/blob/main/examples/02_trials_with_hed.py>`_
     - Adding HED to trials table
   * - `03_events_table_integration.py <https://github.com/VisLab/ndx-hed/blob/main/examples/03_events_table_integration.py>`_
     - Integration with ndx-events EventsTable
   * - `04_bids_conversion.py <https://github.com/VisLab/ndx-hed/blob/main/examples/04_bids_conversion.py>`_
     - Converting BIDS events to NWB with HED
   * - `05_hed_validation.py <https://github.com/VisLab/ndx-hed/blob/main/examples/05_hed_validation.py>`_
     - Comprehensive validation examples
   * - `06_complete_workflow.py <https://github.com/VisLab/ndx-hed/blob/main/examples/06_complete_workflow.py>`_
     - End-to-end workflow demonstration
   * - `07_hed_definitions.py <https://github.com/VisLab/ndx-hed/blob/main/examples/07_hed_definitions.py>`_
     - Custom HED definitions usage

**Running Examples:**

.. code-block:: bash

   # Run individual example
   cd examples
   python 01_basic_hed_classes.py
   
   # Run all examples
   cd examples
   python run_all_examples.py

Integration with NWB Events
---------------------------

The ndx-hed extension works seamlessly with the `ndx-events extension <https://github.com/rly/ndx-events>`_ 
to provide comprehensive event annotation capabilities. HED annotations can be incorporated in three ways:

1. **Direct HED column** - Event-specific annotations
2. **HedValueVector columns** - Shared annotations with value placeholders  
3. **Categorical columns with MeaningsTable** - Category-based annotations

**Example 1: Direct HED Column**

.. code-block:: python

   from ndx_events import EventsTable, DurationVectorData
   from ndx_hed import HedTags
   
   events_table = EventsTable(
       name="stimulus_events", 
       description="Stimulus events with direct HED annotations"
   )
   
   # Add duration column first
   events_table.add_column(
       name="duration",
       description="Event durations",
       data=[],
       col_cls=DurationVectorData,
   )
   
   # Add HED tags column for event-specific annotations
   events_table.add_column(
       name="HED",
       description="HED annotations for each event",
       data=[],
       col_cls=HedTags,
   )
   
   # Add rows of data
   events = [
       {"timestamp": 1.0, "duration": 0.5, "HED": "Eye-blink-artifact"},
       {"timestamp": 25.5, "duration": 3.5, "HED": "Chewing-artifact"},
   ]
   
   for event in events:
       events_table.add_row(event)

**Example 2: HedValueVector Columns**

.. code-block:: python

   from ndx_hed import HedValueVector
   
   events_table = EventsTable(
       name="behavioral_events", 
       description="Events with HedValueVector columns"
   )
   
   # Add intensity column with HED value annotation
   events_table.add_column(
       name="intensity",
       description="Brightness of visual stimulus",
       data=[],
       col_cls=HedValueVector,
       hed="(Luminance, Parameter-value/#)",
   )
   
   # Add reaction time column with HED annotation
   events_table.add_column(
       name="reaction_time",
       description="Participant response time",
       data=[],
       col_cls=HedValueVector,
       hed="(Behavioral-evidence, Parameter-label/Reaction-time, Time-interval/# s)",
   )

**Example 3: Categorical Columns with MeaningsTable**

.. code-block:: python

   from ndx_events import CategoricalVectorData, MeaningsTable
   
   # Create MeaningsTable with HED annotations
   stimulus_meanings = MeaningsTable(
       name="stimulus_type_meanings", 
       description="Meanings and HED annotations for stimulus types"
   )
   
   # Add meaning definitions
   categories = [
       ("circle", "Circular visual stimulus presented at screen center"),
       ("square", "Square visual stimulus presented at screen center"),
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
       ],
       col_cls=HedTags,
   )
   
   # Add categorical column that references the meanings table
   events_table.add_column(
       name="stimulus_type",
       description="Type of visual stimulus presented",
       data=[],
       col_cls=CategoricalVectorData,
       meanings=stimulus_meanings,
   )

See `examples/03_events_table_integration.py <https://github.com/VisLab/ndx-hed/blob/main/examples/03_events_table_integration.py>`_ for detailed demonstrations.

BIDS Compatibility
------------------

`BIDS (Brain Imaging Data Structure) <https://bids.neuroimaging.io/index.html>`_ is a data standard
for organizing neuroimaging and behavioral data from an entire experiment.
The standard uses JSON files called "sidecars" to store metadata associated with its tabular files.

The ndx-hed extension provides utilities to convert between BIDS events files and NWB ``EventsTable`` format:

.. code-block:: python

   from ndx_hed.utils.bids2nwb import extract_meanings, get_events_table, get_bids_events
   import pandas as pd
   import json

   # Convert BIDS to EventsTable
   bids_events_file_path = "Your_events_path_here.tsv"
   bids_sidecar_file_path = "Your_json_sidecar_path_here.json"
   events_df = pd.read_csv(bids_events_file_path, sep="\t")
   
   with open(bids_sidecar_file_path, 'r') as f:
       json_data = json.load(f)
       
   meanings = extract_meanings(json_data)
   events_table = get_events_table("task_events", "Task events", events_df, meanings)

   # Convert EventsTable to BIDS
   bids_df, sidecar_dict = get_bids_events(events_table)

See `examples/04_bids_conversion.py <https://github.com/VisLab/ndx-hed/blob/main/examples/04_bids_conversion.py>`_ for complete examples.

HED Validation
--------------

Creating HED annotations for NWB data and saving these annotations as part of an ``NWBFile`` does not mean 
the annotations are valid. HED validation is performed to ensure they conform to the HED schema:

.. code-block:: python

   from hed.errors import get_printable_issue_string
   from ndx_hed.utils.hed_nwb_validator import HedNWBValidator

   # Create validator and validate entire file
   hed_metadata = HedLabMetaData(hed_schema_version='8.4.0')
   validator = HedNWBValidator(hed_metadata)

   # Assume nwbfile has already been created
   issues = validator.validate_file(nwbfile)

   if not issues:
       print("All HED annotations are valid!")
   else:
       print(f"Validation error: {get_printable_issue_string(issues)}")

**Validation Features:**

* ``HedNWBValidator`` class for comprehensive validation
* Validates HED tags against specified schema version
* Supports both in-memory and file-based validation
* Validates custom definitions
* Provides detailed error reporting

See `examples/05_hed_validation.py <https://github.com/VisLab/ndx-hed/blob/main/examples/05_hed_validation.py>`_ for comprehensive validation examples.

Architecture
------------

Version 0.2.0 introduces a centralized architecture where:

1. ``HedLabMetaData`` is added to the ``NWBFile`` to specify the HED schema version
2. All HED annotations (``HedTags``, ``HedValueVector``) reference this central schema
3. Custom definitions are managed centrally in ``HedLabMetaData``
4. Validation uses the schema and definitions from ``HedLabMetaData``

This ensures consistency across all HED annotations in a file and simplifies schema management.

Use Cases
---------

* **Event Annotation**: Tag experimental events with standardized descriptors
* **Trial Categorization**: Annotate trial types, conditions, and outcomes
* **Stimulus Description**: Describe sensory stimuli with precise semantic tags
* **Behavioral Coding**: Tag participant actions and responses
* **Artifact Marking**: Identify and categorize data artifacts
* **Parametric Data**: Annotate columns with value-based templates
* **Cross-Study Integration**: Enable data pooling with standardized vocabularies

Compatibility
-------------

* **Python**: 3.10+
* **Dependencies**: pynwb>=2.8.2, hdmf>=3.14.1, hedtools>=0.7.1
* **Optional**: ndx-events>=0.4.0 for EventsTable support
* **MATLAB**: Under development (not yet available)

Additional Resources
--------------------

* `HED Standards Organization <https://www.hedtags.org>`_ - Official HED specification and resources
* `HED python tools <https://github.com/hed-standard/hed-python>`_ - Core HED Python library
* `HED annotation in NWB user guide <https://www.hedtags.org/hed-resources/HedAnnotationInNWB.html>`_ - Detailed usage guide
* `NWB documentation <https://pynwb.readthedocs.io/>`_ - PyNWB library documentation
* `ndx-events extension <https://github.com/rly/ndx-events>`_ - Complementary events extension

Contributing
------------

Contributions are welcome! Feel free to submit issues or pull requests to the 
`GitHub repository <https://github.com/VisLab/ndx-hed>`_.
