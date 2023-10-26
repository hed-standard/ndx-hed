"""Unit and integration tests for ndx-hed."""
from datetime import datetime
from dateutil.tz import tzlocal
from hdmf.common import VectorIndex
from pynwb import NWBHDF5IO  # , NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file  # , NWBH5IOFlexMixin
from uuid import uuid4

from ndx_hed import HedAnnotations, HedMetadata


class TestHedMetadataConstructor(TestCase):
    """Simple unit test for creating a HedMetadata."""

    def test_constructor(self):
        """Test setting HedNWBFile values using the constructor."""
        hed_metadata = HedMetadata(hed_schema_version="8.2.0")
        assert hed_metadata.hed_schema_version == "8.2.0"

    def test_add_to_nwbfile(self):
        nwbfile = mock_NWBFile()
        hed_metadata = HedMetadata(hed_schema_version="8.2.0")
        nwbfile.add_lab_meta_data(hed_metadata)
        assert nwbfile.get_lab_meta_data("HedMetadata") is hed_metadata


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
        hed_metadata = HedMetadata(hed_schema_version="8.2.0")
        nwbfile.add_lab_meta_data(hed_metadata)

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_hed_metadata = read_nwbfile.get_lab_meta_data("HedMetadata")
            assert isinstance(read_hed_metadata, HedMetadata)
            assert read_hed_metadata.hed_schema_version == "8.2.0"


# class TestHedNWBFileRoundtripPyNWB(NWBH5IOFlexMixin, TestCase):
#     """Complex, more complete roundtrip test for HedNWBFile using pynwb.testing infrastructure."""

#     def getContainerType(self):
#         return "HedNWBFile"

#     def addContainer(self):
#         self.nwbfile = HedNWBFile(
#             session_description="session_description",
#             identifier=str(uuid4()),
#             session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
#             hed_schema_version="8.2.0",
#         )

#     def getContainer(self, nwbfile: NWBFile):
#         return nwbfile


class TestHedTagsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def test_constructor(self):
        """Test setting HedTags values using the constructor."""
        hed_annotations = HedAnnotations(
            name="name",
            description="description",
            data=["animal_target, correct_response", "animal_target, incorrect_response"],
        )
        assert hed_annotations.name == "name"
        assert hed_annotations.description == "description"
        assert hed_annotations.data == ["animal_target, correct_response", "animal_target, incorrect_response"]

    def test_add_to_trials_table(self):
        """Test adding HedTags column and data to a trials table."""
        nwbfile = mock_NWBFile()
        hed_metadata = HedMetadata(hed_schema_version="8.2.0")
        nwbfile.add_lab_meta_data(hed_metadata)

        nwbfile.add_trial_column("HED", "HED annotations for each trial", col_cls=HedAnnotations)
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="animal_target, correct_response")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="animal_target, incorrect_response")

        assert isinstance(nwbfile.trials["HED"], HedAnnotations)
        assert nwbfile.trials["HED"][0] == "animal_target, correct_response"
        assert nwbfile.trials["HED"][1] == "animal_target, incorrect_response"


class TestHedTagsSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedTags."""

    def setUp(self):
        self.path = "test.nwb"

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """
        Add a HedTags to an NWBFile, write it to file, read the file, and test that the HedTags from the
        file matches the original HedTags.
        """
        nwbfile = mock_NWBFile()
        hed_metadata = HedMetadata(hed_schema_version="8.2.0")
        nwbfile.add_lab_meta_data(hed_metadata)

        nwbfile.add_trial_column("HED", "HED annotations for each trial", col_cls=HedAnnotations)
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="animal_target, correct_response")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="animal_target, incorrect_response")

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_hed_annotations = read_nwbfile.trials["HED"]
            assert isinstance(read_hed_annotations, HedAnnotations)
            # read_nwbfile.trials["hed_tags"][0] is read as a numpy array
            assert read_hed_annotations[0] == "animal_target, correct_response"
            assert read_hed_annotations[1] == "animal_target, incorrect_response"


# class TestHedTagsRoundtripPyNWB(NWBH5IOFlexMixin, TestCase):
#     """Complex, more complete roundtrip test for HedTags using pynwb.testing infrastructure."""

#     def getContainerType(self):
#         return "HedTags"

#     def addContainer(self):
#         self.nwbfile = HedNWBFile(
#             session_description="session_description",
#             identifier=str(uuid4()),
#             session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
#             hed_schema_version="8.2.0",
#         )

#         self.nwbfile.add_trial_column("hed_tags", "HED tags for each trial", col_cls=HedTags, index=True)
#         self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, hed_tags=["animal_target", "correct_response"])
#         self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, hed_tags=["animal_target", "incorrect_response"])

#     def getContainer(self, nwbfile: NWBFile):
#         return nwbfile.trials["hed_tags"].target
