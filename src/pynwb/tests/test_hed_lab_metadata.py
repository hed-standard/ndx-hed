"""Unit and integration tests for ndx-hed."""
import os
from datetime import datetime
from dateutil.tz import tzlocal
from hed import HedSchema
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
        labdata = HedLabMetaData(name='hed_schema', hed_schema_version='8.4.0')
        self.assertIsInstance(labdata, HedLabMetaData)
  
    def test_constructor_empty_version(self):
        """Test create HedLabMetaData with empty schema version."""
        with self.assertRaises(TypeError) as cm:
            HedLabMetaData(name='hed_schema')
        self.assertIn("missing argument", str(cm.exception))

    def test_no_name(self):
        """Test create HedLabMetaData with empty name."""
        schema = HedLabMetaData(hed_schema_version='8.4.0')
        self.assertIsInstance(schema, HedLabMetaData)
        self.assertEqual(schema.name, 'hed_schema')
        self.assertEqual(schema.get_hed_schema_version(), '8.4.0')

    def test_bad_schema_version(self):
        with self.assertRaises(ValueError) as cm:
            HedLabMetaData(name='hed_schema', hed_schema_version='xxxx')
        self.assertIn("Failed to load HED schema version", str(cm.exception))

    def test_bad_name(self):
        with self.assertRaises(ValueError) as cm:
            HedLabMetaData(name='blech', hed_schema_version='8.4.0')
        self.assertIn("The 'name' for HedLabMetaData must be 'hed_schema'", str(cm.exception))

    def test_get_hed_version(self):
        labdata = HedLabMetaData(name='hed_schema', hed_schema_version='8.4.0')
        version = labdata.get_hed_schema_version()
        self.assertEqual('8.4.0', version)

    def test_get_hed_schema_name(self):
        labdata = HedLabMetaData(name='hed_schema', hed_schema_version='8.4.0')
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_two_schema_versions(self):
        """Test creating two HedLabMetaData instances with different schema versions."""
        labdata1 = HedLabMetaData(hed_schema_version='8.4.0')
        labdata2 = HedLabMetaData(hed_schema_version='8.3.0')
        self.assertEqual(labdata1.get_hed_schema_version(), '8.4.0')
        self.assertEqual(labdata2.get_hed_schema_version(), '8.3.0')


class TestHedLabMetaDataRoundTrip(TestCase):

    def setUp(self):
        import tempfile
        fd, self.test_nwb_file_path = tempfile.mkstemp(suffix='.nwb')
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
        hed_info = HedLabMetaData(name="hed_schema", hed_schema_version="8.4.0")
        nwbfile.add_lab_meta_data(hed_info)

        # Write the NWB file
        with NWBHDF5IO(self.test_nwb_file_path, 'w') as io:
            io.write(nwbfile)

        # Read the file back
        with NWBHDF5IO(self.test_nwb_file_path, 'r') as io:
            read_nwbfile = io.read()

            # Access the custom LabMetaData object by its name
            read_hed_info = read_nwbfile.lab_meta_data['hed_schema']
            self.assertIsInstance(read_hed_info, HedLabMetaData)
            self.assertEqual("hed_schema", read_hed_info.name)
            self.assertEqual(read_hed_info.get_hed_schema_version(), "8.4.0")
            schema = read_hed_info.get_hed_schema()
            self.assertIsInstance(schema, HedSchema)

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
