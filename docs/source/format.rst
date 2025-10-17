
.. _ndx-hed:

*******
ndx-hed
*******

Extension Specification
========================

Version |release| |today|

This section provides the technical specification of the ndx-hed extension data types.

Core Data Types
---------------

The ndx-hed extension defines three main data types for integrating HED annotations into NWB files:

HedLabMetaData
~~~~~~~~~~~~~~

**Purpose**: Required container for HED schema metadata and custom definitions.

**Extends**: ``LabMetaData``

**Key Properties**:
- ``hed_schema_version`` (required): HED schema version (e.g., "8.4.0")
- ``hed_definitions`` (optional): Custom HED definitions as string

**Usage**: Must be added to NWBFile before using any HED annotations.

HedTags  
~~~~~~~~

**Purpose**: Row-specific HED annotations for dynamic tables.

**Extends**: ``VectorData``

**Key Properties**:
- ``name``: Must be "HED" (enforced by constructor)
- ``data``: Array of HED tag strings, one per table row
- ``description``: Description of the HED annotations

**Usage**: Add as a column to any DynamicTable (trials, units, epochs, EventsTable, etc.).

HedValueVector
~~~~~~~~~~~~~~

**Purpose**: Column-wide HED templates with value placeholders.

**Extends**: ``VectorData`` 

**Key Properties**:
- ``name``: Custom column name
- ``data``: Array of numeric/categorical values
- ``hed``: HED template string with ``#`` placeholder for values
- ``description``: Description of the data and HED annotation

**Usage**: Creates parametric HED annotations where the template applies to all values in the column.

YAML Schema Files
-----------------

The complete technical specification is defined in YAML files:

- **Schema Definition**: ``spec/ndx-hed.extensions.yaml`` - Complete type definitions
- **Namespace**: ``spec/ndx-hed.namespace.yaml`` - Extension namespace configuration

**View the complete specification**:
- `Schema on GitHub <https://github.com/VisLab/ndx-hed/blob/main/spec/ndx-hed.extensions.yaml>`_
- `Namespace on GitHub <https://github.com/VisLab/ndx-hed/blob/main/spec/ndx-hed.namespace.yaml>`_

Example Usage Patterns
-----------------------

**Basic Setup** (required for all HED usage):

.. code-block:: python

   from ndx_hed import HedLabMetaData
   
   # Add HED metadata to NWB file
   hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")
   nwbfile.add_lab_meta_data(hed_metadata)

**Row-specific annotations**:

.. code-block:: python

   from ndx_hed import HedTags
   
   # Add HED column to trials table  
   nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], 
                           description="HED annotations for trials")

**Template-based annotations**:

.. code-block:: python

   from ndx_hed import HedValueVector
   
   # Create column with HED template
   duration_col = HedValueVector(
       name="duration", data=[1.0, 1.5, 2.0],
       hed="(Sensory-event, Duration/# s)",
       description="Trial durations with HED annotation"
   )

For complete examples, see the `examples directory <https://github.com/VisLab/ndx-hed/tree/main/examples>`_.

Extension Dependencies
----------------------

**Required**:
- ``pynwb >= 2.8.2``
- ``hdmf >= 3.14.1`` 
- ``hedtools >= 0.7.1``

**Optional**:
- ``ndx-events >= 0.4.0`` (for EventsTable integration)

Development and Contribution
-----------------------------

The extension source code and issue tracking is available on `GitHub <https://github.com/VisLab/ndx-hed>`_.

For questions about HED itself, see the `HED Standards Organization <https://www.hedtags.org>`_.
