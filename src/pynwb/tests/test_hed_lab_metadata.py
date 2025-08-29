"""Unit and integration tests for ndx-hed."""
import os
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
import pandas as pd
from hed.errors import HedFileError
from hed import HedSchema
from hdmf.common import DynamicTable, VectorData
from pynwb import NWBHDF5IO, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file
from ndx_hed.hed_lab_metadata import HedLabMetaData
import pytest


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
  

    def test_constructor_empty_data(self):
        """Test create HedLabMetaData with empty schema version."""
        with self.assertRaises(TypeError) as cm:
            HedLabMetaData(name='hed_schema')
        self.assertIn("missing argument", str(cm.exception))

    def test_bad_schema_version(self):
        with self.assertRaises(ValueError) as cm:
            HedLabMetaData(name='blech', hed_schema_version='xxxx')
        self.assertIn("Failed to load HED schema version", str(cm.exception))

    def test_get_hed_version(self):
        labdata = HedLabMetaData(name='hed_schema', hed_schema_version='8.4.0')
        version = labdata.get_hed_schema_version()
        self.assertEqual('8.4.0', version)

    def test_get_hed_schema_name(self):
        labdata = HedLabMetaData(name='hed_schema', hed_schema_version='8.4.0')
        schema = labdata.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

class TestHedLabMetaDataRoundTrip(TestCase):
   
    def get_temp_nwb_file_path(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.nwb')
        os.close(fd)
        return path

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
        test_nwb_file_path = self.get_temp_nwb_file_path()
        try:
            with NWBHDF5IO(test_nwb_file_path, 'w') as io:
                io.write(nwbfile)

            # Read the file back
            with NWBHDF5IO(test_nwb_file_path, 'r') as io:
                read_nwbfile = io.read()
                
                # Access the custom LabMetaData object by its name
                read_hed_info = read_nwbfile.lab_meta_data['hed_schema']
                self.assertIsInstance(read_hed_info, HedLabMetaData)
                self.assertEqual("hed_schema", read_hed_info.name)
                self.assertEqual(read_hed_info.get_hed_schema_version(), "8.4.0")
                schema = read_hed_info.get_hed_schema()
                self.assertIsInstance(schema, HedSchema)
                
        finally:
            if os.path.exists(test_nwb_file_path):
                os.remove(test_nwb_file_path)


# class TestHedLabMetadataSimpleRoundtrip(TestCase):
#     """Simple roundtrip test for HedNWBFile."""

#     def setUp(self):
#         self.path = "test.nwb"
#         nwb_mock = mock_NWBFile()
#         nwb_mock.add_trial_column(name="HED", hed_version="8.2.0", description="HED annotations for each trial",
#                                   col_cls=HedTags, data=[])
#         nwb_mock.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
#         nwb_mock.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
#         self.nwb_mock = nwb_mock

#     def tearDown(self):
#         remove_test_file(self.path)

#     def test_roundtrip(self):
#         """  Create a HedLabMetaData, write it to mock file, read file, and test matches the original HedNWBFile."""

#         with NWBHDF5IO(self.path, mode="w") as io:
#             io.write(self.nwb_mock)

#         with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
#             read_nwbfile = io.read()
#             hed_col = read_nwbfile.trials["HED"]
#             self.assertIsInstance(hed_col, HedTags)
#             self.assertEqual(hed_col.get_hed_version(), "8.2.0")
#             self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
#             self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")


# class TestHedTagsNWBFileRoundtrip(TestCase):
#     """Simple roundtrip test for HedTags."""

#     def setUp(self):
#         self.path = "test.nwb"
#         self.start_time = datetime(1970, 1, 1, 12, tzinfo=tzutc())
#         self.ref_time = datetime(1979, 1, 1, 0, tzinfo=tzutc())
#         self.filename = 'test_nwbfileio.h5'
#         self.nwbfile = NWBFile(session_description='a test NWB File',
#                                identifier='TEST123',
#                                session_start_time=self.start_time,
#                                timestamps_reference_time=self.ref_time,
#                                file_create_date=datetime.now(tzlocal()),
#                                experimenter='test experimenter',
#                                stimulus_notes='test stimulus notes',
#                                data_collection='test data collection notes',
#                                experiment_description='test experiment description',
#                                institution='nomad',
#                                lab='nolab',
#                                notes='nonotes',
#                                pharmacology='nopharmacology',
#                                protocol='noprotocol',
#                                related_publications='nopubs',
#                                session_id='007',
#                                slices='noslices',
#                                source_script='nosources',
#                                surgery='nosurgery',
#                                virus='novirus',
#                                source_script_file_name='nofilename')

#         self.nwbfile.add_trial_column(name="HED", description="HED annotations for each trial",
#                                       hed_version="8.2.0", col_cls=HedTags, data=[])
#         self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
#         self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")

#     def tearDown(self):
#         remove_test_file(self.path)

#     def test_roundtrip(self):
#         """
#         Add a HedTags to an NWBFile, write it to file, read the file, and test that the HedTags from the
#         file matches the original HedTags.
#         """

#         with NWBHDF5IO(self.path, mode="w") as io:
#             io.write(self.nwbfile)

#         with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
#             read_nwbfile = io.read()
#             tags = read_nwbfile.trials["HED"]
#             schema = tags.get_hed_schema()
#             self.assertIsInstance(schema, HedSchema)
#             self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
#             self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")
