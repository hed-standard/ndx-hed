"""Unit and integration tests for ndx-hed."""
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
import pandas as pd
from hed.errors import HedFileError
from hed import HedSchema
from hdmf.common import DynamicTable, VectorData
from pynwb import NWBHDF5IO, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file
from ndx_hed.hed_tags import HedTags


class TestHedTagsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        tags = HedTags(hed_version='8.2.0', data=["Correct-action", "Incorrect-action"])
        self.assertEqual(tags.name, "HED")
        self.assertTrue(tags.description)
        self.assertEqual(tags.data, ["Correct-action", "Incorrect-action"])

    def test_constructor_empty_data(self):
        """Test setting HED values using the constructor."""
        tags = HedTags(hed_version='8.2.0', data=[])
        self.assertEqual(tags.name, "HED")
        self.assertTrue(tags.description)
        self.assertFalse(tags.data)

    def test_bad_schema_version(self):
        """Test setting with bad schema and valid values."""
        with self.assertRaises(HedFileError) as cm:
            HedTags(hed_version='blech', data=["Correct-action", "Incorrect-action"])
        self.assertEqual(f'SCHEMA_VERSION_INVALID', cm.exception.args[0])

    def test_constructor_bad_data(self):
        """Test setting HED values using the constructor."""
        with self.assertRaises(ValueError) as cm:
            HedTags(hed_version='8.2.0', data=["Blech, Red"])
        self.assertIn("InvalidHEDData", str(cm.exception))

    def test_add_row(self):
        """Testing adding a row to the HedTags. """
        tags = HedTags(hed_version='8.2.0', data=["Correct-action", "Incorrect-action"])
        self.assertEqual(len(tags.data), 2)
        tags.add_row(val="Correct-action")
        self.assertEqual(len(tags.data), 3)

    def test_add_bad_row(self):
        tags = HedTags(hed_version='8.2.0', data=["Correct-action", "Incorrect-action"])
        with self.assertRaises(ValueError) as cm:
            tags.add_row(val="Blech, (Red, Blue)")
        self.assertIn("InvalidHEDValue", str(cm.exception))

    def test_get(self):
        """Testing getting slices. """
        tags = HedTags(hed_version='8.2.0', data=["Correct-action", "Incorrect-action"])
        self.assertEqual(tags.get(0), "Correct-action")
        self.assertEqual(tags.get([0, 1]), ['Correct-action', 'Incorrect-action'])

    def test_temp(self):
        tags = HedTags(hed_version='8.3.0', data=["Correct-action", "Incorrect-action"])
        tags.add_row("Sensory-event, Visual-presentation")

    def test_dynamic_table(self):
        """Add a HED column to a DynamicTable."""
        my_table = DynamicTable(
            name='bands',
            description='band info for LFPSpectralAnalysis',
            columns=[HedTags(hed_version='8.2.0', data=[])])
        my_table.add_row(data={"HED": "Red,Green"})
        self.assertEqual(my_table["HED"].data[0], "Red,Green")
        self.assertIsInstance(my_table["HED"], HedTags)
        my_table.add_column(hed_version="8.2.0", name="Blech", description="Another HedTags column",
                            col_cls=HedTags, data=["White,Black"])
        self.assertEqual(my_table["Blech"].data[0], "White,Black")

        color_nums = VectorData(name="color_code", description="Integers representing colors", data=[1,2,3])
        color_tags = HedTags(name="HED", hed_version="8.2.0", data=["Red", "Green", "Blue"])
        color_table = DynamicTable(
            name="colors",
            description="Colors for the experiment",
            columns=[color_nums, color_tags])
        self.assertEqual(color_table[0, "HED"], "Red")
        my_list = color_table[0]
        self.assertIsInstance(my_list, pd.DataFrame)

    def test_add_to_trials_table(self):
        """ Test adding HED column and data to a trials table."""
        nwbfile = mock_NWBFile()
        nwbfile.add_trial_column(name="HED", hed_version="8.2.0", col_cls=HedTags, data=[], description="temp")
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.assertIsInstance(nwbfile.trials["HED"], HedTags)
        hed_col = nwbfile.trials["HED"]
        self.assertEqual(hed_col.name, "HED")
        self.assertEqual(hed_col.description, "temp")
        self.assertEqual(nwbfile.trials["HED"].data[0], "Correct-action")
        self.assertEqual(nwbfile.trials["HED"].data[1], "Incorrect-action")

        nwbfile.add_trial_column(name="Blech", description="HED column", hed_version="8.2.0", col_cls=HedTags,
                                 data=["Red", "Blue"])
        nwbfile.add_trial(start_time=5.0, stop_time=6.0, HED="Black", Blech="Sensory-event")
        nwbfile.add_trial(start_time=7.0, stop_time=8.0, HED="Red", Blech="Agent-action")
        self.assertIsInstance(nwbfile.trials["Blech"], HedTags)
        hed_col = nwbfile.trials["Blech"]
        self.assertEqual(hed_col.name, "Blech")
        self.assertIsInstance(nwbfile.trials["Blech"], HedTags)
        self.assertEqual(hed_col.description, "HED column")
        self.assertEqual(nwbfile.trials["Blech"].data[0], "Red")
        self.assertEqual(nwbfile.trials["Blech"].data[1], "Blue")

    def test_get_hed_version(self):
        tags = HedTags(hed_version='8.2.0', data=["Correct-action", "Incorrect-action"])
        version = tags.get_hed_version()
        self.assertEqual('8.2.0', version)


class TestHedTagsSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedNWBFile."""

    def setUp(self):
        self.path = "test.nwb"
        nwb_mock = mock_NWBFile()
        nwb_mock.add_trial_column(name="HED", hed_version="8.2.0", description="HED annotations for each trial",
                                  col_cls=HedTags, data=[])
        nwb_mock.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwb_mock.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.nwb_mock = nwb_mock

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """  Create a HedMetadata, write it to mock file, read file, and test matches the original HedNWBFile."""

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwb_mock)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            hed_col = read_nwbfile.trials["HED"]
            self.assertIsInstance(hed_col, HedTags)
            self.assertEqual(hed_col.get_hed_version(), "8.2.0")
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")


class TestHedTagsNWBFileRoundtrip(TestCase):
    """Simple roundtrip test for HedTags."""

    def setUp(self):
        self.path = "test.nwb"
        self.start_time = datetime(1970, 1, 1, 12, tzinfo=tzutc())
        self.ref_time = datetime(1979, 1, 1, 0, tzinfo=tzutc())
        self.filename = 'test_nwbfileio.h5'
        self.nwbfile = NWBFile(session_description='a test NWB File',
                               identifier='TEST123',
                               session_start_time=self.start_time,
                               timestamps_reference_time=self.ref_time,
                               file_create_date=datetime.now(tzlocal()),
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

        self.nwbfile.add_trial_column(name="HED", description="HED annotations for each trial",
                                      hed_version="8.2.0", col_cls=HedTags, data=[])
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
            tags = read_nwbfile.trials["HED"]
            schema = tags.get_hed_schema()
            self.assertIsInstance(schema, HedSchema)
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")
