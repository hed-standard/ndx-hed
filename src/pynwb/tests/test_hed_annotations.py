"""Unit and integration tests for ndx-hed."""
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
from hed.schema import HedSchema, HedSchemaGroup
from pynwb import NWBFile, NWBHDF5IO, get_manager  # , NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file  # , NWBH5IOFlexMixin
from src.pynwb.ndx_hed import HedAnnotations, HedVersion


class TestHedVersion(TestCase):
    """Simple unit test for creating a HedMetadata."""

    def test_constructor(self):
        """Test setting HedNWBFile values using the constructor."""
        hed_version1 = HedVersion(["8.2.0"])
        print(f"HED version: {str(hed_version1.version)}")
        print(f"{str(hed_version1)}")
        self.assertIsInstance(hed_version1.version, list)
        schema1 = hed_version1.get_hed_schema()
        self.assertIsInstance(schema1, HedSchema)
        hed_version2 = HedVersion(["8.2.0", "sc:score_1.0.0"])
        schema2 = hed_version2.get_hed_schema()
        self.assertIsInstance(schema2, HedSchemaGroup)

    def test_add_to_nwbfile(self):
        nwbfile = mock_NWBFile()
        hed_version1 = HedVersion(["8.2.0"])
        nwbfile.add_lab_meta_data(hed_version1)
        hed_version2 = nwbfile.get_lab_meta_data("hed_version")
        self.assertIsInstance(hed_version2, HedVersion)


class TestHedNWBFileSimpleRoundtrip(TestCase):
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
        hed_version = HedVersion(["8.2.0"])
        nwbfile.add_lab_meta_data(hed_version)
        print(f"nwb: {str(nwbfile)}")
        print(f"{str(hed_version)}")

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(nwbfile)

        # with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
        #     read_nwbfile = io.read()
        #     print(f"nwb: {str(read_nwbfile)}")
        #     read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
        #     self.assertIsInstance(read_hed_version, HedVersion)
        #     self.assertEqual(read_hed_version.hed_version, "8.2.0")


# # class TestHedNWBFileRoundtripPyNWB(NWBH5IOFlexMixin, TestCase):
# #     """Complex, more complete roundtrip test for HedNWBFile using pynwb.testing infrastructure."""
# 
# #     def getContainerType(self):
# #         return "HedNWBFile"
# 
# #     def addContainer(self):
# #         self.nwbfile = HedNWBFile(
# #             session_description="session_description",
# #             identifier=str(uuid4()),
# #             session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
# #             hed_schema_version="8.2.0",
# #         )
# 
# #     def getContainer(self, nwbfile: NWBFile):
# #         return nwbfile
#

class TestHedAnnotationsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        hed_annotations = HedAnnotations(
            name='HED',
            description="description",
            data=["animal_target, correct_response", "animal_target, incorrect_response"],
        )
        print(f"{hed_annotations}")
        self.assertEqual(hed_annotations.sub_name, "HED")
        self.assertEqual(hed_annotations.description, "description")
        self.assertEqual(hed_annotations.data,["animal_target, correct_response", "animal_target, incorrect_response"])

    def test_add_to_trials_table(self):
        """Test adding HED column and data to a trials table."""
        nwbfile = mock_NWBFile()
        hed_version = HedVersion(["8.2.0"])
        nwbfile.add_lab_meta_data(hed_version)
        #nwbfile.add_trial_column("HED", "HED annotations for each trial")
        nwbfile.add_trial_column(name="HED", description="HED annotations for each trial", 
                                 col_cls=HedAnnotations, data=[])
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="animal_target, correct_response")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="animal_target, incorrect_response")

        self.assertIsInstance(nwbfile.trials["HED"], HedAnnotations)
        print(f"{str(nwbfile)}")
        print(f"{str(nwbfile.trials)}")
        hed_col = nwbfile.trials["HED"]
        print(f"hed_col: {str(hed_col.data)}")
        self.assertEqual(nwbfile.trials["HED"].data[0], "animal_target, correct_response")
        self.assertEqual(nwbfile.trials["HED"].data[1], "animal_target, incorrect_response")

class TestHedTagsSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedTags."""

    def setUp(self):
        self.path = "test.nwb"
        self.start_time = datetime(1970, 1, 1, 12, tzinfo=tzutc())
        self.ref_time = datetime(1979, 1, 1, 0, tzinfo=tzutc())
        self.create_date = datetime(2017, 4, 15, 12, tzinfo=tzlocal())
        self.manager = get_manager()
        self.filename = 'test_nwbfileio.h5'
        self.nwbfile = NWBFile(session_description='a test NWB File',
                               identifier='TEST123',
                               session_start_time=self.start_time,
                               timestamps_reference_time=self.ref_time,
                               file_create_date=self.create_date,
                               experimenter='test experimenter',
                               stimulus_notes='test stimulus notes',
                               data_collection='test data collection notes',
                               experiment_description='test experiment description',
                               institution='nomad',
                               lab='nolab',
                               notes='nonotes',
                               pharmacology='nopharmacology',
                               protocol='noprotocol',
                               related_publications='nopubs',
                               session_id='007',
                               slices='noslices',
                               source_script='nosources',
                               surgery='nosurgery',
                               virus='novirus',
                               source_script_file_name='nofilename')

    def tearDown(self):
        remove_test_file(self.path)

    def test_hed_version(self):
        hed1 = HedVersion(["8.2.0"])
        self.assertIsInstance(hed1, HedVersion)
        schema = hed1.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

#     def test_roundtrip(self):
#         """
#         Add a HedTags to an NWBFile, write it to file, read the file, and test that the HedTags from the
#         file matches the original HedTags.
#         """
#         hed_version = HedVersion(["8.2.0"])
#         self.nwbfile.add_lab_meta_data(hed_version)
# 
#         self.nwbfile.add_trial_column("HED", "HED annotations for each trial")
#         self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="animal_target, correct_response")
#         self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="animal_target, incorrect_response")
#         print("to here")
#         # nwbfile = mock_NWBFile()
#         # hed_version = HedVersion(hed_schema_version="8.2.0")
#         # nwbfile.add_lab_meta_data(hed_version)
#         # 
#         # nwbfile.add_trial_column("HED", "HED annotations for each trial", col_cls=HedAnnotations)
#         # nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="animal_target, correct_response")
#         # nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="animal_target, incorrect_response")
#         
#         # with NWBHDF5IO(self.path, mode="w") as io:
#         #     io.write(nwbfile)
#         # 
#         # with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
#         #     read_nwbfile = io.read()
#         #     read_hed_annotations = read_nwbfile.trials["HED"]
#         #     assert isinstance(read_hed_annotations, HedAnnotations)
#         #     # read_nwbfile.trials["hed_tags"][0] is read as a numpy array
#         #     assert read_hed_annotations[0] == "animal_target, correct_response"
#         #     assert read_hed_annotations[1] == "animal_target, incorrect_response"
# 
# 
# # class TestHedTagsRoundtripPyNWB(NWBH5IOFlexMixin, TestCase):
# #     """Complex, more complete roundtrip test for HedTags using pynwb.testing infrastructure."""
# 
# #     def getContainerType(self):
# #         return "HedTags"
# 
# #     def addContainer(self):
# #         self.nwbfile = HedNWBFile(
# #             session_description="session_description",
# #             identifier=str(uuid4()),
# #             session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
# #             hed_schema_version="8.2.0",
# #         )
# 
# #         self.nwbfile.add_trial_column("hed_tags", "HED tags for each trial", col_cls=HedTags, index=True)
# #         self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, hed_tags=["animal_target", "correct_response"])
# #         self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, hed_tags=["animal_target", "incorrect_response"])
# 
# #     def getContainer(self, nwbfile: NWBFile):
# #         return nwbfile.trials["hed_tags"].target
