Overview
========

The **ndx-hed** extension integrates HED (Hierarchical Event Descriptors) annotations into NWB (Neurodata Without Borders) neurophysiology data files. HED provides a standardized vocabulary for annotating events and experimental metadata with precise, machine-readable semantic tags.

.. note::
   * For installation and quick start instructions, see the `README.md <https://github.com/hed-standard/ndx-hed/blob/main/README.md>`_
   * For runnable examples and usage patterns, see the `examples README <https://github.com/hed-standard/ndx-hed/blob/main/examples/README.md>`_
   * All examples can be run directly from the ``examples/`` directory

Key Features
------------

**Three Core Classes:**

1. **HedLabMetaData** - Required metadata container
   
   * Stores HED schema version for the entire NWB file
   * Supports both standard and library schemas
   * Manages custom HED definitions
   * Must be added to `NWBFile` before using any HED annotations

2. **HedTags** - Row-specific annotations
   
   * Extends NWB ``VectorData`` class
   * Stores one HED string per table row
   * Must be named "HED" (enforced by constructor)
   * Works with any NWB ``DynamicTable`` (trials, units, epochs, etc.)

3. **HedValueVector** - Column-wide template annotations
   
   * Stores numerical/categorical data with HED templates
   * Uses ``#`` placeholder for values (e.g., "Duration/# s")
   * HED annotation applies to entire column
   * Ideal for parametric annotations

**Validation System:**

* ``HedNWBValidator`` class for comprehensive validation
* Validates HED tags against specified schema version
* Supports both in-memory and file-based validation
* Validates custom definitions
* Provides detailed error reporting

**BIDS Integration:**

* Bidirectional conversion between BIDS events and NWB ``EventsTable``
* Extract HED from BIDS JSON sidecars
* Convert categorical columns with meanings tables
* Preserve HED annotations during format conversion

**ndx-events Integration:**

* Full support for ``EventsTable``, ``MeaningsTable``, ``CategoricalVectorData``
* Three integration patterns:
  
  1. Direct HED column for event-specific annotations
  2. HedValueVector columns for shared annotations with values
  3. Categorical columns with HED in MeaningsTable

Architecture
------------

Version 0.2.0 introduces a centralized architecture where:

1. ``HedLabMetaData`` is added to the `NWBFile` to specify the HED schema version
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

Resources
---------

* `HED Standards <https://www.hedtags.org>`_
* `NWB Format <https://www.nwb.org>`_
* `GitHub Repository <https://github.com/hed-standard/ndx-hed>`_
* `HED Resources Documentation <https://www.hed-resources.org/en/latest/HedAnnotationInNWB.html>`_
