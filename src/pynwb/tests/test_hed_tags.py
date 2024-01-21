"""Unit and integration tests for ndx-hed."""
from pandas import DataFrame
from datetime import datetime, timezone
from dateutil.tz import tzlocal, tzutc
from uuid import uuid4, UUID
from hed.schema import HedSchema, HedSchemaGroup, load_schema_version
from hdmf.common import VectorData
from hdmf.utils import docval, getargs, get_docval, popargs
from pynwb import NWBHDF5IO, get_manager, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file, NWBH5IOFlexMixin
from ndx_hed import HedVersion, HedTags


class TestHedTagsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def setUp(self):
        self.tags = HedTags(data=["Correct-action", "Incorrect-action"])

    def tearDown(self):
        pass

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        self.assertEqual(self.tags.name, "HED")
        self.assertTrue(self.tags.description)
        self.assertEqual(self.tags.data, ["Correct-action", "Incorrect-action"])

    def test_add_row(self):
        """Testing adding a row to the HedTags. """
        self.assertEqual(len(self.tags.data), 2)
        self.tags.add_row("Correct-action")
        self.assertEqual(len(self.tags.data), 3)

    def test_get(self):
        """Testing getting slices. """
        self.assertEqual(self.tags.get(0), "Correct-action")
        self.assertEqual(self.tags.get([0, 1]), ['Correct-action', 'Incorrect-action'])

    def test_add_to_trials_table(self):
        """Test adding HED column and data to a trials table."""
        nwbfile = mock_NWBFile()
        nwbfile.add_trial_column(name="HED", description="temp", col_cls=HedTags, data=[])
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.assertIsInstance(nwbfile.trials["HED"], HedTags)
        hed_col = nwbfile.trials["HED"]
        self.assertEqual(hed_col.name, "HED")
        self.assertEqual(hed_col.description, "temp")
        self.assertEqual(nwbfile.trials["HED"].data[0], "Correct-action")
        self.assertEqual(nwbfile.trials["HED"].data[1], "Incorrect-action")

    def test_add_to_trials_table_force_HED(self):
        """Trial table does not allow the forcing of the column name to be HED."""
        nwbfile = mock_NWBFile()
        nwbfile.add_trial_column(name="Blech", description="temp", col_cls=HedTags, data=[])
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, Blech="Correct-action")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, Blech="Incorrect-action")
        self.assertIsInstance(nwbfile.trials["Blech"], HedTags)
        hed_col = nwbfile.trials["Blech"]
        self.assertEqual(hed_col.name, "HED")
        self.assertEqual(nwbfile.trials["Blech"].data[0], "Correct-action")
        self.assertEqual(nwbfile.trials["Blech"].data[1], "Incorrect-action")

    def test_validate_hed_tags(self):
        """Test the validate_hed_tags"""
        schema = load_schema_version("8.2.0")
        issues = self.tags.validate(schema)
        self.assertFalse(issues)
        self.tags.add_row("Blech")
        self.tags.add_row("Sensory-event")
        self.tags.add_row("")
        self.tags.add_row("Agent-action")
        self.tags.add_row("Red, (Blue, Green")
        issues = self.tags.validate(schema)
        self.assertEqual(7, len(self.tags.data))
        self.assertTrue(issues)

    def test_get_root(self):
        root = self.tags._get_root()
        self.assertFalse(root)

    def test_get_hed_version(self):
        schema = self.tags.get_hed_schema()
        self.assertFalse(schema)


class TestHedTagsSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedNWBFile."""

    def setUp(self):
        self.path = "test.nwb"
        nwb_mock = mock_NWBFile()
        nwb_mock.add_lab_meta_data(HedVersion("8.2.0"))
        nwb_mock.add_trial_column(name="HED", description="HED annotations for each trial",
                                  col_cls=HedTags, data=[])
        nwb_mock.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwb_mock.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.nwb_mock = nwb_mock

    def tearDown(self):
        remove_test_file(self.path)

    def test_get_root(self):
        tags = self.nwb_mock.trials["HED"]
        self.assertIsInstance(tags, HedTags)
        root = tags._get_root()
        self.assertIsInstance(root, NWBFile)

    def test_get_hed_schema(self):
        tags = self.nwb_mock.trials["HED"]
        schema = tags.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_validate_hed_tags(self):
        """Test the validate_hed_tags"""
        schema = load_schema_version("8.2.0")
        tags = self.nwb_mock.trials["HED"]
        issues = tags.validate(schema)
        self.assertFalse(issues)
        tags.add_row("Blech")
        tags.add_row("Sensory-event")
        tags.add_row("")
        tags.add_row("Agent-action")
        tags.add_row("Red, (Blue, Green")
        self.assertEqual(7, len(self.nwb_mock.trials["HED"]))
        issues = tags.validate(schema)
        self.assertEqual(7, len(tags.data))
        self.assertTrue(issues)

    def test_roundtrip(self):
        """  Create a HedMetadata, write it to mock file, read file, and test that it matches the original HedNWBFile."""

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwb_mock)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
            self.assertIsInstance(read_hed_version, HedVersion)
            self.assertEqual(read_hed_version.version, "8.2.0")
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")


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

    def test_get_root(self):
        tags = self.nwbfile.trials["HED"]
        self.assertIsInstance(tags, HedTags)
        root = tags._get_root()
        self.assertIsInstance(root, NWBFile)

    def test_get_hed_schema(self):
        tags = self.nwbfile.trials["HED"]
        schema = tags.get_hed_schema()
        self.assertIsInstance(schema, HedSchema)

    def test_validate_hed_tags(self):
        """Test the validate_hed_tags"""
        schema = load_schema_version("8.2.0")
        tags = self.nwbfile.trials["HED"]
        issues = tags.validate(schema)
        self.assertFalse(issues)
        tags.add_row("Blech")
        tags.add_row("Sensory-event")
        tags.add_row("")
        tags.add_row("Agent-action")
        tags.add_row("Red, (Blue, Green")
        self.assertEqual(7, len(self.nwbfile.trials["HED"]))
        issues = tags.validate(schema)
        self.assertEqual(7, len(tags.data))
        self.assertTrue(issues)
    def test_roundtrip(self):
        """
        Add a HedTags to an NWBFile, write it to file, read the file, and test that the HedTags from the
        file matches the original HedTags.
        """

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwbfile)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_hed_version = read_nwbfile.get_lab_meta_data("hed_version")
            self.assertIsInstance(read_hed_version, HedVersion)
            self.assertEqual(read_hed_version.version, "8.2.0")
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")
