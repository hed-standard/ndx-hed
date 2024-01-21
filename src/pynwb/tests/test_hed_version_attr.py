"""Unit and integration tests for ndx-hed."""
from datetime import datetime, timezone
from dateutil.tz import tzlocal, tzutc
from uuid import uuid4, UUID
from pynwb.file import LabMetaData
from pynwb import NWBHDF5IO, get_manager, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file, NWBH5IOFlexMixin
from ndx_hed import HedVersionAttr
from hed.schema import HedSchema, HedSchemaGroup


class TestHedVersionAttr(TestCase):
    """Simple unit test for creating a HedMetadata."""

    def test_constructor(self):
        """Test setting HedNWBFile values using the constructor."""
        hed_version_example = HedVersionAttr("8.2.0")
        self.assertIsInstance(hed_version_example, HedVersionAttr)
        self.assertIsInstance(hed_version_example, LabMetaData)
        self.assertEqual(hed_version_example.name, "hed_version")
        self.assertIsInstance(hed_version_example.version, str)
        self.assertEqual(hed_version_example.version, "8.2.0")
        self.assertIsInstance(hed_version_example.schema_string, str)
        # hed_version2 = HedVersion(["8.2.0"])
        # self.assertIsInstance(hed_version2.version, list)
        # hed_version3 = HedVersion(["8.2.0", "sc:score_1.0.0"])

    def test_get_schema(self):
        hed_version_example = HedVersionAttr(version="8.2.0")
        self.assertEqual(hed_version_example.name, "hed_version")
        hed_schema = hed_version_example.get_schema()
        self.assertIsInstance(hed_schema, HedSchema)

    def test_get_version(self):
        hed_version_example = HedVersionAttr(version="8.2.0")
        version = hed_version_example.get_version()
        self.assertIsInstance(version, str)
        self.assertEqual(version, "8.2.0")

    def test_add_to_nwbfile(self):
        nwbfile = mock_NWBFile()
        hed_version_example = HedVersionAttr(version="8.2.0")
        nwbfile.add_lab_meta_data(lab_meta_data=hed_version_example)
        hed_version_new = nwbfile.get_lab_meta_data(hed_version_example.name)
        self.assertIsInstance(hed_version_new, HedVersionAttr)
        # hed_version2 = HedVersion(["8.2.0"])


class TestHedVersionSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedNWBFile."""

    def setUp(self):
        self.path = "test.nwb"

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """
        Create a HedMetadata, write it to file, read the file, and test that it matches the original HedNWBFile.
        """
        nwbfile = mock_NWBFile()
        hed_version_example = HedVersionAttr(version="8.2.0")
        nwbfile.add_lab_meta_data(lab_meta_data=hed_version_example)
        hed_version_new = nwbfile.get_lab_meta_data("hed_version")
        self.assertIsInstance(hed_version_new, HedVersionAttr)
        self.assertEqual(hed_version_new.name, "hed_version")
        self.assertEqual(hed_version_new.version, "8.2.0")
        self.assertIsInstance(hed_version_new, HedVersionAttr)
        self.assertIsInstance(hed_version_new, LabMetaData)
        schema = hed_version_new.get_schema()
        self.assertIsInstance(schema, HedSchema)

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_hed_version = read_nwbfile.get_lab_meta_data(hed_version_example.name)
            # self.assertIsInstance(read_hed_version, HedVersionAttr)
            # self.assertEqual(read_hed_version.version, "8.2.0")


# class TestHedVersionNWBFileSimpleRoundtrip(TestCase):
#     """Simple roundtrip test for HedTags."""
# 
#     def setUp(self):
#         self.path = "test.nwb"
#         self.start_time = datetime(1970, 1, 1, 12, tzinfo=tzutc())
#         self.ref_time = datetime(1979, 1, 1, 0, tzinfo=tzutc())
#         self.create_date = datetime(2017, 4, 15, 12, tzinfo=tzlocal())
#         self.manager = get_manager()
#         self.filename = 'test_nwbfileio.h5'
#         self.nwbfile = NWBFile(session_description='a test NWB File',
#                                identifier='TEST123',
#                                session_start_time=self.start_time,
#                                timestamps_reference_time=self.ref_time,
#                                file_create_date=self.create_date,
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
#         hed_version = HedVersion(version="8.2.0")
#         self.nwbfile.add_lab_meta_data(hed_version)
#         print(f"Name:{hed_version.name}")
# 
#     def tearDown(self):
#         remove_test_file(self.path)
# 
#     def test_version(self):
#         hed_version = self.nwbfile.get_lab_meta_data("hed_version")
#         self.assertIsInstance(hed_version, HedVersion)
#         schema = hed_version.get_schema()
#         self.assertIsInstance(schema, HedSchema)
# 
#     def test_roundtrip(self):
#         print(self.nwbfile)
#         with NWBHDF5IO(self.path, mode="w") as io:
#             io.write(self.nwbfile)
# 
#         with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
#             read_nwbfile = io.read()
#             print(read_nwbfile)
#             read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
#             #self.assertIsInstance(read_hed_version, HedVersion)
#             self.assertEqual(read_hed_version.version, "8.2.0")
