"""Unit and integration tests for ndx-hed."""

import os
from datetime import datetime
from dateutil.tz import tzlocal
from hed.schema import HedSchema, HedSchemaGroup
from hed.models import DefinitionDict
from pynwb import NWBHDF5IO, NWBFile
from pynwb.testing import TestCase, remove_test_file
from ndx_hed.hed_lab_metadata import HedLabMetaData


class TestHedLabMetaDataConstructor(TestCase):
    """Simple unit test for creating a HedLabMetaData."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        self.assertIsInstance(labdata, HedLabMetaData)

    def test_constructor_with_definitions(self):
        """Test creating HedLabMetaData with definitions parameter."""
        definitions = "(Definition/TestEvent, (Sensory-event, Visual-presentation))"
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)
        self.assertIsInstance(labdata, HedLabMetaData)
        self.assertIsInstance(labdata.definitions, str)
        self.assertEqual(len(labdata._definition_dict.defs), 1)
        self.assertIn("testevent", labdata.definitions)

    def test_constructor_with_two_definitions(self):
        """Test creating HedLabMetaData with definitions parameter."""
        test_definitions = "(Definition/apple,(Item)),(Definition/orange,(Item))"
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=test_definitions)
        self.assertIsInstance(labdata, HedLabMetaData)
        # Note: DefinitionDict normalizes the format, so we need to expect the normalized version
        expected_normalized = "(Definition/apple,(Item)),(Definition/orange,(Item))"
        self.assertEqual(labdata.definitions, expected_normalized)

    def test_constructor_empty_version(self):
        """Test create HedLabMetaData with empty schema version."""
        with self.assertRaises(TypeError) as cm:
            HedLabMetaData(name="hed_schema")
        self.assertIn("missing argument", str(cm.exception))

    def test_no_name(self):
        """Test create HedLabMetaData with empty name."""
        schema = HedLabMetaData(hed_schema_version="8.4.0")
        self.assertIsInstance(schema, HedLabMetaData)
        self.assertEqual(schema.name, "hed_schema")
        self.assertEqual(schema.get_hed_schema_version(), "8.4.0")

    def test_bad_schema_version(self):
        with self.assertRaises(ValueError) as cm:
            HedLabMetaData(hed_schema_version="xxxx")
        self.assertIn("Failed to load HED schema version", str(cm.exception))

    def test_get_hed_version(self):
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        version = labdata.get_hed_schema_version()
        self.assertEqual("8.4.0", version)

    def test_get_hed_schema_name(self):
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_two_schema_versions(self):
        """Test creating two HedLabMetaData instances with different schema versions."""
        labdata1 = HedLabMetaData(hed_schema_version="8.4.0")
        labdata2 = HedLabMetaData(hed_schema_version="8.3.0")
        self.assertEqual(labdata1.get_hed_schema_version(), "8.4.0")
        self.assertEqual(labdata2.get_hed_schema_version(), "8.3.0")

    def test_constructor_without_definitions(self):
        """Test creating HedLabMetaData without definitions parameter."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        self.assertIsInstance(labdata, HedLabMetaData)
        self.assertIsNone(labdata.definitions)

    def test_constructor_with_library_schemas(self):
        """Test creating HedLabMetaData with library schema versions."""
        library_schema_version = '["score_2.1.0","lang_1.1.0"]'
        labdata = HedLabMetaData(hed_schema_version=library_schema_version)
        self.assertIsInstance(labdata, HedLabMetaData)
        self.assertEqual(labdata.get_hed_schema_version(), library_schema_version)
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_constructor_with_library_schemas_and_definitions(self):
        """Test creating HedLabMetaData with library schemas and definitions."""
        library_schema_version = '["score_2.1.0","lang_1.1.0"]'
        test_definitions = "(Definition/apple,(Item)),(Definition/orange,(Item))"
        labdata = HedLabMetaData(hed_schema_version=library_schema_version, definitions=test_definitions)
        self.assertIsInstance(labdata, HedLabMetaData)
        self.assertEqual(labdata.get_hed_schema_version(), library_schema_version)
        extracted_defs = labdata.definitions
        self.assertEqual(extracted_defs, test_definitions)
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_constructor_with_prefixed_schema_and_library(self):
        """Test creating HedLabMetaData with prefixed standard and library schemas."""
        mixed_schema_version = '["bc:8.4.0","score_2.1.0"]'
        labdata = HedLabMetaData(hed_schema_version=mixed_schema_version)
        self.assertIsInstance(labdata, HedLabMetaData)
        self.assertEqual(labdata.get_hed_schema_version(), mixed_schema_version)
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchemaGroup)

    def test_get_definition_dict(self):
        """Test getting the DefinitionDict from HedLabMetaData."""
        test_definitions = "Red, Blue"
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=test_definitions)
        definition_dict = labdata.get_definition_dict()
        self.assertIsInstance(definition_dict, DefinitionDict)

    def test_add_definitions_method(self):
        """Test the add_definitions method."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        additional_defs = "Orange/Red: Another test definition."
        labdata.add_definitions(additional_defs)
        # The method should execute without error


class TestHedLabMetaDataRoundTrip(TestCase):

    def setUp(self):
        import tempfile

        fd, self.test_nwb_file_path = tempfile.mkstemp(suffix=".nwb")
        os.close(fd)

    def tearDown(self):
        remove_test_file(self.test_nwb_file_path)

    def test_roundtrip_lab_metadata(self):
        # Create an NWB file and an instance of HedLabMetaData
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing HedLabMetaData",
            identifier="Testing metadata",
            session_start_time=session_start,
        )

        # Instantiate the class and add the lab_infor
        hed_info = HedLabMetaData(hed_schema_version="8.4.0")
        nwbfile.add_lab_meta_data(hed_info)

        # Write the NWB file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read the file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()

            # Access the custom LabMetaData object by its name
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]
            self.assertIsInstance(read_hed_info, HedLabMetaData)
            self.assertEqual("hed_schema", read_hed_info.name)
            self.assertEqual(read_hed_info.get_hed_schema_version(), "8.4.0")
            schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(schema, HedSchema)

    def test_roundtrip_lab_metadata_with_definitions(self):
        # Create an NWB file and an instance of HedLabMetaData with definitions
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing HedLabMetaData with definitions",
            identifier="Testing metadata with definitions",
            session_start_time=session_start,
        )

        # Instantiate the class with definitions and add the lab_info
        test_definitions = "(Definition/apple,(Item)),(Definition/orange,(Item/Fruit))"
        hed_info = HedLabMetaData(hed_schema_version="8.4.0", definitions=test_definitions)
        nwbfile.add_lab_meta_data(hed_info)

        # Write the NWB file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read the file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()

            # Access the custom LabMetaData object by its name
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]
            self.assertIsInstance(read_hed_info, HedLabMetaData)
            self.assertEqual("hed_schema", read_hed_info.name)
            self.assertEqual(read_hed_info.get_hed_schema_version(), "8.4.0")
            # Note: This test might need format adjustment for the normalized definitions
            self.assertEqual(read_hed_info.definitions, test_definitions)
            schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(schema, HedSchema)

    def test_roundtrip_lab_metadata_with_library_schemas(self):
        """Test roundtrip functionality with library schema versions."""
        # Create an NWB file and an instance of HedLabMetaData with library schemas
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing HedLabMetaData with library schemas",
            identifier="Testing library schemas",
            session_start_time=session_start,
        )

        # Instantiate the class with library schemas
        library_schema_version = '["score_2.1.0","lang_1.1.0"]'
        hed_info = HedLabMetaData(hed_schema_version=library_schema_version)
        nwbfile.add_lab_meta_data(hed_info)

        # Write the NWB file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read the file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()

            # Access the custom LabMetaData object by its name
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]
            self.assertIsInstance(read_hed_info, HedLabMetaData)
            self.assertEqual("hed_schema", read_hed_info.name)
            self.assertEqual(read_hed_info.get_hed_schema_version(), library_schema_version)
            schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(schema, HedSchema)

    def test_roundtrip_lab_metadata_with_library_schemas_and_definitions(self):
        """Test roundtrip functionality with library schemas and definitions."""
        # Create an NWB file and an instance of HedLabMetaData
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing HedLabMetaData with library schemas and definitions",
            identifier="Testing library schemas with definitions",
            session_start_time=session_start,
        )

        # Instantiate the class with library schemas and definitions
        library_schema_version = '["bc:8.4.0","score_2.1.0"]'
        test_definitions = "(Definition/apple,(Item/Fruit)),(Definition/orange,(Item/Fruit))"
        hed_info = HedLabMetaData(
            hed_schema_version=library_schema_version, definitions=test_definitions
        )
        nwbfile.add_lab_meta_data(hed_info)

        # Write the NWB file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read the file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()

            # Access the custom LabMetaData object by its name
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]
            self.assertIsInstance(read_hed_info, HedLabMetaData)
            self.assertEqual("hed_schema", read_hed_info.name)
            self.assertEqual(read_hed_info.get_hed_schema_version(), library_schema_version)
            self.assertEqual(read_hed_info.definitions, test_definitions)
            schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(schema, HedSchemaGroup)

    def test_add_two(self):
        # Create an NWB file and an instance of HedLabMetaData
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing HedLabMetaData",
            identifier="Testing metadata",
            session_start_time=session_start,
        )

        # Instantiate the class and add the lab_infor
        hed_info1 = HedLabMetaData(hed_schema_version="8.4.0")
        nwbfile.add_lab_meta_data(hed_info1)
        hed_info2 = HedLabMetaData(hed_schema_version="8.3.0")
        with self.assertRaises(ValueError) as cm:
            nwbfile.add_lab_meta_data(hed_info2)
        self.assertIn("Cannot add <class 'ndx_hed.hed_lab_metadata.HedLabMetaData'> 'hed_schema' ", str(cm.exception))


class TestHedLabMetaDataDefinitions(TestCase):
    """Comprehensive tests for definitions handling in HedLabMetaData."""

    def setUp(self):
        self.test_nwb_file_path = "test_hed_lab_metadata_definitions.nwb"

    def tearDown(self):
        remove_test_file(self.test_nwb_file_path)

    def test_definitions_none(self):
        """Test HedLabMetaData with no definitions."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        self.assertIsNone(labdata.definitions)
        self.assertIsNone(labdata.definitions)
        # The DefinitionDict should exist but be empty
        self.assertEqual(len(labdata._definition_dict), 0)

    def test_definitions_empty_string(self):
        """Test HedLabMetaData with empty definitions string."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions="")
        self.assertIsNone(labdata.definitions)
        self.assertIsNone(labdata.definitions)

    def test_definitions_whitespace_string(self):
        """Test HedLabMetaData with whitespace-only definitions string."""
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions="   \n  \t  ")
        self.assertIsNone(labdata.definitions)
        self.assertIsNone(labdata.definitions)

    def test_definitions_single_definition(self):
        """Test HedLabMetaData with a single definition."""
        definitions = "(Definition/testevent,(Sensory-event,Visual-presentation))"
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)

        # Check that definitions field contains the normalized format
        self.assertEqual(labdata.definitions, definitions)

        # Check internal DefinitionDict structure
        self.assertIsInstance(labdata._definition_dict, DefinitionDict)
        self.assertEqual(len(labdata._definition_dict.defs), 1)
        self.assertIn("testevent", labdata._definition_dict.defs)

        # Check DefinitionEntry details
        entry = labdata._definition_dict.defs["testevent"]
        self.assertEqual(entry.name, "testevent")
        self.assertFalse(entry.takes_value)
        self.assertIn("Sensory-event", str(entry.contents))
        self.assertIn("Visual-presentation", str(entry.contents))

        # Check get_definitions returns the same string
        extracted = labdata.definitions
        self.assertEqual(extracted, definitions)

    def test_definitions_with_library_schemas(self):
        """Test definitions with library schema versions."""
        library_schema_version = '["score_2.1.0","lang_1.1.0"]'
        definitions = "(Definition/mytask,(Task))"
        labdata = HedLabMetaData(hed_schema_version=library_schema_version, definitions=definitions)

        self.assertIsInstance(labdata.definitions, str)
        self.assertEqual(len(labdata._definition_dict.defs), 1)
        self.assertIn("mytask", labdata._definition_dict.defs)

        # Check that schema is HedSchema for library schemas
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

        # Check roundtrip
        extracted = labdata.definitions
        self.assertEqual(extracted, definitions)

    def test_multiple_definitions(self):
        """List of definitions."""
        definitions = "(Definition/event1,(Sensory-event)),(Definition/event2/#,(Parameter-value/#))"
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)

        self.assertIsInstance(labdata.definitions, str)
        self.assertEqual(len(labdata._definition_dict.defs), 2)
        entry1 = labdata._definition_dict.defs["event1"]
        self.assertEqual(entry1.name, "event1")
        self.assertFalse(entry1.takes_value)
        entry2 = labdata._definition_dict.defs["event2"]
        self.assertEqual(entry2.name, "event2")
        self.assertTrue(entry2.takes_value)
        extracted = labdata.definitions
        self.assertEqual(extracted, definitions)

    def test_definitions_add_method(self):
        """Test adding definitions using add_definitions method."""
        # Start with no definitions
        labdata = HedLabMetaData(hed_schema_version="8.4.0")
        self.assertIsNone(labdata.definitions)

        # Add definitions
        definitions = "(Definition/addedevent, (Move))"
        labdata.add_definitions(definitions)

        self.assertIsInstance(labdata.definitions, str)
        self.assertEqual(len(labdata._definition_dict.defs), 1)
        self.assertIn("addedevent", labdata._definition_dict.defs)

        # Add more definitions
        more_definitions = "(Definition/secondevent, (Red))"
        labdata.add_definitions(more_definitions)

        self.assertEqual(len(labdata._definition_dict.defs), 2)
        self.assertIn("addedevent", labdata._definition_dict.defs)
        self.assertIn("secondevent", labdata._definition_dict.defs)

    def test_definitions_roundtrip_file_io(self):
        """Test that definitions survive file write/read cycles."""
        # Create NWB file with definitions
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing definitions roundtrip",
            identifier="definitions_io_test",
            session_start_time=session_start,
        )

        definitions = "(Definition/FileIOTest,(Sensory-event)),(Definition/ResponseEvent/#,(Parameter-value/#))"
        hed_info = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)
        nwbfile.add_lab_meta_data(hed_info)

        # Write file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]

            # Verify definitions structure
            self.assertIsInstance(read_hed_info.definitions, str)
            self.assertEqual(len(read_hed_info._definition_dict.defs), 2)
            self.assertIn("fileiotest", read_hed_info._definition_dict.defs)
            self.assertIn("responseevent", read_hed_info._definition_dict.defs)

            # Verify exact roundtrip
            extracted = read_hed_info.definitions
            self.assertIn("fileiotest", extracted)
            self.assertIn("responseevent", extracted)

            # Verify individual entries
            test_entry = read_hed_info._definition_dict.defs["fileiotest"]
            self.assertEqual(test_entry.name, "fileiotest")
            self.assertFalse(test_entry.takes_value)

            response_entry = read_hed_info._definition_dict.defs["responseevent"]
            self.assertEqual(response_entry.name, "responseevent")
            self.assertTrue(response_entry.takes_value)

    def test_definitions_roundtrip_with_library_schemas_file_io(self):
        """Test definitions with library schemas survive file write/read cycles."""
        # Create NWB file with library schemas and definitions
        session_start = datetime.now(tzlocal())
        nwbfile = NWBFile(
            session_description="Testing library schemas + definitions roundtrip",
            identifier="library_definitions_io_test",
            session_start_time=session_start,
        )

        library_schema_version = '["8.4.0","bc:score_2.1.0"]'
        definitions = "(Definition/librarytest,(Task-activity,Walk))"
        hed_info = HedLabMetaData(hed_schema_version=library_schema_version, definitions=definitions)
        self.assertEqual(hed_info.definitions, definitions)
        nwbfile.add_lab_meta_data(hed_info)

        # Write file
        with NWBHDF5IO(self.test_nwb_file_path, "w") as io:
            io.write(nwbfile)

        # Read file back
        with NWBHDF5IO(self.test_nwb_file_path, "r") as io:
            read_nwbfile = io.read()
            read_hed_info = read_nwbfile.lab_meta_data["hed_schema"]

            self.assertIsInstance(read_hed_info, HedLabMetaData)
            # Verify schema and definitions
            hed_schema_version = read_hed_info.get_hed_schema_version()
            self.assertEqual(hed_schema_version, library_schema_version)
            hed_schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(hed_schema, HedSchemaGroup)

            # Verify definitions structure
            extracted = read_hed_info.definitions
            self.assertIsInstance(extracted, str)
            self.assertIn("librarytest", extracted)

            # Verify exact roundtrip
            self.assertEqual(extracted, definitions)

    def test_definitions_invalid_hed_syntax(self):
        """Test handling of invalid HED syntax in definitions."""
        with self.assertRaises(Exception):
            # Invalid HED syntax - missing closing parenthesis
            invalid_definitions = "(Definition/BadEvent, (Sensory-event"
            HedLabMetaData(hed_schema_version="8.4.0", definitions=invalid_definitions)

    def test_definitions_consistency_across_operations(self):
        """Test that definitions remain consistent across all operations."""
        definitions = "(Definition/consistencytest,(Sensory-event)),(Definition/valuetest/#,(Parameter-value/#))"

        # Test constructor
        labdata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)
        initial_extracted = labdata.definitions
        self.assertIn("consistencytest", initial_extracted)
        # Test adding to existing definitions
        additional_def = "(Definition/additionaltest,(Move))"
        labdata.add_definitions(additional_def)

        # Original definitions should still be present (checking lowercase normalized names)
        updated_extracted = labdata.definitions
        self.assertIn("consistencytest", updated_extracted)
        self.assertIn("valuetest", updated_extracted)
        self.assertIn("additionaltest", updated_extracted)

        # Should have 3 definitions now
        self.assertEqual(len(labdata._definition_dict.defs), 3)
