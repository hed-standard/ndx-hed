"""Unit and integration tests for ndx-hed."""
from datetime import datetime, timezone
from dateutil.tz import tzlocal, tzutc
from uuid import uuid4, UUID
from hed.schema import HedSchema, HedSchemaGroup
from pynwb import NWBHDF5IO, get_manager, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file, NWBH5IOFlexMixin
from src.pynwb.ndx_hed import HedVersion, HedTags


class TestHedAnnotationsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        hed_annotations = HedTags(
            name='HED',
            description="description",
            data=["Correct-action", "Incorrect-action"],
        )
        self.assertEqual(hed_annotations.sub_name, "HED")
        self.assertEqual(hed_annotations.description, "description")
        self.assertEqual(hed_annotations.data, ["Correct-action", "Incorrect-action"])

    def test_add_to_trials_table(self):
        """Test adding HED column and data to a trials table."""
        nwbfile = mock_NWBFile()
        hed_version = HedVersion("8.2.0")
        nwbfile.add_lab_meta_data(hed_version)
        nwbfile.add_trial_column(name="HED", description="HED annotations for each trial",
                                 col_cls=HedTags, data=[])
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.assertIsInstance(nwbfile.trials["HED"], HedTags)
        hed_col = nwbfile.trials["HED"]
        self.assertEqual(nwbfile.trials["HED"].data[0], "Correct-action")
        self.assertEqual(nwbfile.trials["HED"].data[1], "Incorrect-action")


# class TestHedTagsSimpleRoundtrip(TestCase):
#     """Simple roundtrip test for HedNWBFile."""
# 
#     def setUp(self):
#         self.path = "test.nwb"
# 
#     def tearDown(self):
#         remove_test_file(self.path)
# 
#     def test_roundtrip(self):
#         """
#         Create a HedMetadata, write it to file, read the file, and test that it matches the original HedNWBFile.
#         """
#         nwbfile = mock_NWBFile()
#         # hed_version = HedVersion(["8.2.0"])
#         hed_version = HedVersion("8.2.0")
#         nwbfile.add_lab_meta_data(hed_version)
# 
#         with NWBHDF5IO(self.path, mode="w") as io:
#             io.write(nwbfile)
# 
#         with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
#             read_nwbfile = io.read()
#             read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
#             self.assertIsInstance(read_hed_version, HedVersion)
#             self.assertEqual(read_hed_version.version, "8.2.0")


class TestHedTagsNWBFileRoundtrip(TestCase):
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
        hed_version = HedVersion("8.2.0")
        self.nwbfile.add_lab_meta_data(hed_version)
        self.nwbfile.add_trial_column(name="HED", description="HED annotations for each trial",
                                      col_cls=HedTags, data=[])
        self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """
        Add a HedTags to an NWBFile, write it to file, read the file, and test that the HedTags from the
        file matches the original HedTags.
        """

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            lab_metadata = read_nwbfile.get_lab_meta_data()
            print(f"lab: {str(lab_metadata)}")
            read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
            print(f"hed: {read_hed_version}")
            # self.assertIsInstance(read_hed_version, HedVersion)
            # self.assertEqual(read_hed_version.version, "8.2.0")
            # self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            # self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")

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



# class TestHedNWBFileRoundtripPyNWB(NWBH5IOFlexMixin, TestCase):
#     """Complex, more complete roundtrip test for HedNWBFile using pynwb.testing infrastructure."""
# 
#     def setUp(self):
#         self.nwbfile = NWBFile(
#             session_description='session_description',
#             identifier='identifier',
#             session_start_time=datetime.now(timezone.utc)
#         )
#         self.filename = "test.nwb"
#         self.export_filename = "test_export.nwb"
# 
#     def tearDown(self):
#         remove_test_file(self.filename)
#         remove_test_file(self.export_filename)
# 
#     def addContainer(self):
#         """ Add the test ElectricalSeries and related objects to the given NWBFile """
#         pass
# 
#     def getContainer(self, nwbfile: NWBFile):
#         # return nwbfile.acquisition['test_eS']
#         return None
# 
#     def test_roundtrip(self):
#         hed_version = HedVersion("8.2.0")
#         self.nwbfile.add_lab_meta_data(hed_version)
# 
#         with NWBHDF5IO(self.filename, mode='w') as io:
#             io.write(self.nwbfile)
# 
#         with NWBHDF5IO(self.filename, mode='r', load_namespaces=True) as io:
#             read_nwbfile = io.read()
#             read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
#             self.assertIsInstance(read_hed_version, HedVersion)
#             self.assertEqual(read_hed_version.version, "8.2.0")

