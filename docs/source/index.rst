ndx-hed: HED Integration for NWB
=================================

.. raw:: html

   <div class="badge-container">
      <a href="https://doi.org/10.5281/zenodo.13142816"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.13142816.svg" alt="DOI"></a>
      <a href="https://badge.fury.io/py/ndx-hed"><img src="https://badge.fury.io/py/ndx-hed.svg" alt="PyPI version"></a>
      <a href="https://codecov.io/gh/hed-standard/ndx-hed"><img src="https://codecov.io/gh/hed-standard/ndx-hed/branch/main/graph/badge.svg" alt="codecov"></a>
   </div>

**ndx-hed** is a `Neurodata Without Borders (NWB) <https://www.nwb.org/>`_ extension that integrates 
`HED (Hierarchical Event Descriptors) <https://www.hedtags.org>`_ annotations into neurophysiology data files.
HED provides a standardized vocabulary for annotating events and experimental metadata with precise, 
machine-readable semantic tags.

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: 🚀 Quick Start
      :link: description
      :link-type: doc

      Get started with HED annotations in NWB files. Learn the basic concepts and see simple examples.

   .. grid-item-card:: 📚 API Reference 
      :link: api
      :link-type: doc

      Complete API documentation for all classes and functions in the ndx-hed extension.

   .. grid-item-card:: 🔧 Examples
      :link: https://github.com/VisLab/ndx-hed/tree/main/examples
      :link-type: url

      Comprehensive runnable examples showing real-world usage patterns and best practices.

   .. grid-item-card:: 📋 Extension Spec
      :link: format
      :link-type: doc

      Technical specification of the NWB extension data types and their structure.

Installation
------------

.. tab-set::

   .. tab-item:: Python

      .. code-block:: bash

         pip install -U ndx-hed

   .. tab-item:: Development

      .. code-block:: bash

         git clone https://github.com/VisLab/ndx-hed.git
         cd ndx-hed
         pip install -e .

Quick Example
-------------

.. code-block:: python

   from pynwb import NWBFile
   from ndx_hed import HedLabMetaData, HedTags
   from datetime import datetime

   # Create NWB file with HED metadata
   nwbfile = NWBFile(
       session_description="Example session with HED annotations",
       identifier="example_session_001", 
       session_start_time=datetime.now()
   )

   # Add HED schema metadata (required)
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

Main Classes
------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Class
     - Purpose
     - Use Cases
   * - **HedLabMetaData**
     - HED schema specification and lab-specific definitions
     - Required for all HED validation
   * - **HedTags** 
     - Row-specific HED annotations
     - Row-specific tags in any DynamicTable
   * - **HedValueVector**
     - Column-wide HED templates
     - Shared annotations with value placeholders (#)

Key Features
------------

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: 🏷️ Standardized Annotations
      
      Use HED's hierarchical vocabulary to create precise, machine-readable annotations for events, stimuli, and behaviors.

   .. grid-item-card:: ✅ Built-in Validation
      
      Comprehensive validation system ensures HED annotations conform to schema specifications.

   .. grid-item-card:: 🔄 BIDS Integration
      
      Seamless conversion between BIDS events files and NWB EventsTable format with HED preservation.

   .. grid-item-card:: 🧩 NWB Integration
      
      Works with any NWB DynamicTable and integrates with ndx-events EventsTable for comprehensive event annotation.

Resources
---------

* `HED Standards Organization <https://www.hedtags.org>`_ - Official HED specification and resources
* `HED Annotation in NWB Guide <https://www.hed-resources.org/en/latest/HedAnnotationInNWB.html>`_ - Detailed usage guide
* `NWB Documentation <https://pynwb.readthedocs.io/>`_ - PyNWB library documentation
* `ndx-events Extension <https://github.com/rly/ndx-events>`_ - Complementary events extension

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Documentation

   description
   api

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Extension Specification

   format

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Project Info

   release_notes
   credits

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
