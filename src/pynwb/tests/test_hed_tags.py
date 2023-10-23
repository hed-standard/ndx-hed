"""Unit and integration tests for ndx-hed."""
from datetime import datetime
from dateutil.tz import tzlocal
from hdmf.common import VectorIndex
from pynwb import NWBHDF5IO  # , NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file  # , NWBH5IOFlexMixin
from uuid import uuid4

from ndx_hed import HedTags, HedNWBFile


class TestHedNWBFileConstructor(TestCase):
    """Simple unit test for creating a HedNWBFile."""

    def test_constructor(self):
        """Test setting HedNWBFile values using the constructor."""
        hed_nwbfile = HedNWBFile(
            session_description="session_description",
            identifier=str(uuid4()),
            session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
            hed_schema_version="8.2.0",
        )
        assert hed_nwbfile.hed_schema_version == "8.2.0"


class TestHedNWBFileSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedNWBFile."""

    def setUp(self):
        self.path = "test.nwb"

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """
        Create a HedNWBFile, write it to file, read the file, and test that it matches the original HedNWBFile.
        """
        hed_nwbfile = HedNWBFile(
            session_description="session_description",
            identifier=str(uuid4()),
            session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
            hed_schema_version="8.2.0",
        )

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(hed_nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            assert isinstance(read_nwbfile, HedNWBFile)
            assert read_nwbfile.hed_schema_version == "8.2.0"


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
        hed_tags = HedTags(
            name="name",
            description="description",
            data=["tag1", "tag2"],
        )
        assert hed_tags.name == "name"
        assert hed_tags.description == "description"
        assert hed_tags.data == ["tag1", "tag2"]

    def test_add_to_trials_table(self):
        """Test adding HedTags column and data to a trials table."""
        nwbfile = mock_NWBFile()
        nwbfile.add_trial_column("hed_tags", "HED tags for each trial", col_cls=HedTags, index=True)
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, hed_tags=["tag1", "tag2"])
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, hed_tags=["tag1", "tag3"])

        assert isinstance(nwbfile.trials["hed_tags"], VectorIndex)
        assert isinstance(nwbfile.trials["hed_tags"].target, HedTags)
        assert nwbfile.trials["hed_tags"][0] == ["tag1", "tag2"]
        assert nwbfile.trials["hed_tags"][0] == ["tag1", "tag2"]


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
        hed_nwbfile = HedNWBFile(
            session_description="session_description",
            identifier=str(uuid4()),
            session_start_time=datetime(1970, 1, 1, tzinfo=tzlocal()),
            hed_schema_version="8.2.0",
        )

        hed_nwbfile.add_trial_column("hed_tags", "HED tags for each trial", col_cls=HedTags, index=True)
        hed_nwbfile.add_trial(start_time=0.0, stop_time=1.0, hed_tags=["tag1", "tag2"])
        hed_nwbfile.add_trial(start_time=2.0, stop_time=3.0, hed_tags=["tag1", "tag3"])

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(hed_nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            assert isinstance(read_nwbfile, HedNWBFile)
            assert isinstance(read_nwbfile.trials["hed_tags"], VectorIndex)
            assert isinstance(read_nwbfile.trials["hed_tags"].target, HedTags)
            # read_nwbfile.trials["hed_tags"][0] is read as a numpy array
            assert all(read_nwbfile.trials["hed_tags"][0] == ["tag1", "tag2"])
            assert all(read_nwbfile.trials["hed_tags"][1] == ["tag1", "tag3"])


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
#         self.nwbfile.add_trial(start_time=0.0, stop_time=1.0, hed_tags=["tag1", "tag2"])
#         self.nwbfile.add_trial(start_time=2.0, stop_time=3.0, hed_tags=["tag1", "tag3"])

#     def getContainer(self, nwbfile: NWBFile):
#         return nwbfile.trials["hed_tags"].target
