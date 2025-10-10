"""Unit and integration tests for ndx-hed."""

import pandas as pd
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
from pynwb.core import DynamicTable, VectorData
from pynwb import NWBHDF5IO, NWBFile
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing import TestCase, remove_test_file
from ndx_hed.hed_tags import HedTags, HedValueVector


class TestHedTagsConstructor(TestCase):
    """Simple unit test for creating a HedTags."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        """Test setting HED values using the constructor."""
        tags = HedTags(data=["Correct-action", "Incorrect-action"])
        self.assertEqual(tags.name, "HED")
        self.assertTrue(tags.description)
        self.assertEqual(tags.data, ["Correct-action", "Incorrect-action"])

    def test_constructor_empty_data(self):
        """Test setting HED values using the constructor."""
        tags = HedTags(data=[])
        self.assertEqual(tags.name, "HED")
        self.assertTrue(tags.description)
        self.assertFalse(tags.data)

    def test_constructor_bad_data(self):
        """Test setting HED values using the constructor."""
        with self.assertRaises(TypeError) as cm:
            HedTags(data=43)
        self.assertIn("incorrect type", str(cm.exception))

    def test_add_row(self):
        """Testing adding a row to the HedTags."""
        tags = HedTags(data=["Correct-action", "Incorrect-action"])
        self.assertEqual(len(tags.data), 2)
        tags.add_row(val="Correct-action")
        self.assertEqual(len(tags.data), 3)

    def test_add_bad_row(self):
        tags = HedTags(data=[46])
        with self.assertRaises(TypeError) as cm:
            tags.add_row(val=[[43], 45])
        self.assertIn("incorrect type", str(cm.exception))

    def test_get(self):
        """Testing getting slices."""
        tags = HedTags(data=["Correct-action", "Incorrect-action"])
        self.assertEqual(tags.get(0), "Correct-action")
        self.assertEqual(tags.get([0, 1]), ["Correct-action", "Incorrect-action"])

    def test_temp(self):
        tags = HedTags(data=["Correct-action", "Incorrect-action"])
        tags.add_row("Sensory-event, Visual-presentation")

    def test_dynamic_table(self):
        """Add a HED column to a DynamicTable."""
        my_table = DynamicTable(name="bands", description="band info0", columns=[HedTags(data=[])])
        my_table.add_row(data={"HED": "Red,Green"})
        self.assertEqual(my_table["HED"].data[0], "Red,Green")
        self.assertIsInstance(my_table["HED"], HedTags)

    def test_dynamic_table_bad_hedName(self):
        my_table = DynamicTable(name="bands", description="band info1")
        with self.assertRaises(ValueError) as cm:
            my_table.add_column(
                name="Blech", description="Another HedTags column", col_cls=HedTags, data=["White,Black"]
            )
        self.assertIn("The 'name' for HedTags must be 'HED'", str(cm.exception))

    def test_dynamic_table_multiple_columns(self):
        color_nums = VectorData(name="color_code", description="Integers representing colors", data=[1, 2, 3])
        color_tags = HedTags(data=["Red", "Green", "Blue"])
        color_table = DynamicTable(
            name="colors", description="Colors for the experiment", columns=[color_nums, color_tags]
        )
        self.assertEqual(color_table[0, "HED"], "Red")
        my_list = color_table[0]
        self.assertIsInstance(my_list, pd.DataFrame)

    def test_add_to_trials_table(self):
        """Test adding HED column and data to a trials table."""
        nwbfile = mock_NWBFile()
        nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="temp")
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.assertIsInstance(nwbfile.trials["HED"], HedTags)
        hed_col = nwbfile.trials["HED"]
        self.assertEqual(hed_col.name, "HED")
        self.assertEqual(hed_col.description, "temp")
        self.assertEqual(nwbfile.trials["HED"].data[0], "Correct-action")
        self.assertEqual(nwbfile.trials["HED"].data[1], "Incorrect-action")

        with self.assertRaises(ValueError) as cm:
            nwbfile.add_trial_column(name="Blech", description="HED annotations", col_cls=HedTags, data=["Red", "Blue"])
        self.assertIn("The 'name' for HedTags must be 'HED'", str(cm.exception))


class TestHedTagsSimpleRoundtrip(TestCase):
    """Simple roundtrip test for HedNWBFile."""

    def setUp(self):
        self.path = "test.nwb"
        nwb_mock = mock_NWBFile()
        nwb_mock.add_trial_column(name="HED", description="HED annotations for each trial", col_cls=HedTags, data=[])
        nwb_mock.add_trial(start_time=0.0, stop_time=1.0, HED="Correct-action")
        nwb_mock.add_trial(start_time=2.0, stop_time=3.0, HED="Incorrect-action")
        self.nwb_mock = nwb_mock

    def tearDown(self):
        remove_test_file(self.path)

    def test_roundtrip(self):
        """Create a HedMetadata, write it to mock file, read file, and test matches the original HedNWBFile."""

        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwb_mock)

        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            hed_col = read_nwbfile.trials["HED"]
            self.assertIsInstance(hed_col, HedTags)
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")


class TestHedTagsNWBFileRoundtrip(TestCase):
    """Simple roundtrip test for HedTags."""

    def setUp(self):
        self.path = "test.nwb"
        self.start_time = datetime(1970, 1, 1, 12, tzinfo=tzutc())
        self.ref_time = datetime(1979, 1, 1, 0, tzinfo=tzutc())
        self.filename = "test_nwbfileio.h5"
        self.nwbfile = NWBFile(
            session_description="a test NWB File",
            identifier="TEST123",
            session_start_time=self.start_time,
            timestamps_reference_time=self.ref_time,
            file_create_date=datetime.now(tzlocal()),
            experimenter="test experimenter",
            stimulus_notes="test stimulus notes",
            data_collection="test data collection notes",
            experiment_description="test experiment description",
            institution="nomad",
            lab="nolab",
            notes="nonotes",
            pharmacology="nopharmacology",
            protocol="noprotocol",
            related_publications="nopubs",
            session_id="007",
            slices="noslices",
            source_script="nosources",
            surgery="nosurgery",
            virus="novirus",
            source_script_file_name="nofilename",
        )

        self.nwbfile.add_trial_column(
            name="HED", description="HED annotations for each trial", col_cls=HedTags, data=[]
        )
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
            self.assertIsInstance(tags, HedTags)
            self.assertEqual(read_nwbfile.trials["HED"].data[0], "Correct-action")
            self.assertEqual(read_nwbfile.trials["HED"].data[1], "Incorrect-action")


class TestHedValueVectorConstructor(TestCase):
    """Unit tests for creating a HedValueVector."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        """Test setting HED value vector using the constructor."""
        values = HedValueVector(
            name="test_values",
            description="Test value vector",
            data=[1, 2, 3, 4],
            hed="Label/#, Sensory-event, Visual-presentation",
        )
        self.assertEqual(values.name, "test_values")
        self.assertEqual(values.description, "Test value vector")
        self.assertEqual(values.data, [1, 2, 3, 4])
        self.assertEqual(values.hed, "Label/#, Sensory-event, Visual-presentation")

    def test_constructor_empty_data(self):
        """Test setting HED value vector with empty data."""
        values = HedValueVector(name="empty_values", description="Empty value vector",
                                data=[], hed="Agent-action, Label/#")
        self.assertEqual(values.name, "empty_values")
        self.assertEqual(values.description, "Empty value vector")
        self.assertFalse(values.data)
        self.assertEqual(values.hed, "Agent-action, Label/#")

    def test_constructor_no_hed(self):
        """Test creating HedValueVector without HED annotation."""
        with self.assertRaises(TypeError) as cm:
            HedValueVector(name="no_hed_values", description="Values without HED", data=[1, 2, 3])
        self.assertIn("missing argument", str(cm.exception))

    def test_constructor_string_data(self):
        """Test HedValueVector with string data."""
        values = HedValueVector(
            name="string_values",
            description="String value vector",
            data=["red", "green", "blue"],
            hed="Sensory-event, Visual-presentation, Color, Label/#",
        )
        self.assertEqual(values.data, ["red", "green", "blue"])
        self.assertEqual(values.hed, "Sensory-event, Visual-presentation, Color, Label/#")

    def test_constructor_numeric_data(self):
        """Test HedValueVector with numeric data."""
        values = HedValueVector(
            name="numeric_values",
            description="Numeric value vector",
            data=[1.5, 2.7, 3.9],
            hed="Measurement, Parameter-value/#",
        )
        self.assertEqual(values.data, [1.5, 2.7, 3.9])
        self.assertEqual(values.hed, "Measurement, Parameter-value/#")

    def test_add_to_dynamic_table(self):
        """Test adding HedValueVector to a DynamicTable."""
        values = HedValueVector(
            name="intensity",
            description="Stimulus intensity values",
            data=[10, 20, 30],
            hed="Sensory-event, Parameter-value/#",
        )

        table = DynamicTable(name="stimulus_table", description="Table with stimulus data", columns=[values])

        self.assertEqual(len(table.columns), 1)
        self.assertIsInstance(table["intensity"], HedValueVector)
        self.assertEqual(table["intensity"].hed, "Sensory-event, Parameter-value/#")

    def test_different_data_types(self):
        """Test HedValueVector with different data types."""
        # Test boolean data
        bool_values = HedValueVector(
            name="bool_data", description="Boolean values", data=[True, False, True],
            hed="(Parameter-name/Logical-value,Label/#)"
        )
        self.assertEqual(bool_values.data, [True, False, True])

        # Test mixed numeric data (should work with VectorData)
        mixed_values = HedValueVector(
            name="mixed_data", description="Mixed numeric values", data=[1, 2.5, 3, 4.7], hed="Parameter-value/#"
        )
        self.assertEqual(mixed_values.data, [1, 2.5, 3, 4.7])

    def test_hed_attribute_access(self):
        """Test accessing and modifying the hed attribute."""
        values = HedValueVector(
            name="test_access", description="Test attribute access", data=[1, 2, 3], hed="Label/#"
        )

        # Test initial value
        self.assertEqual(values.hed, "Label/#")

        # Test modification (not allowed, should raise AttributeError)
        with self.assertRaises(AttributeError):
            values.hed = "Label/#, Red"


class TestHedValueVectorRoundtrip(TestCase):
    """Test roundtrip functionality for HedValueVector with NWBFile."""

    def setUp(self):
        """Set up test NWBFile."""

        self.path = "test.nwb"
        self.nwbfile = NWBFile(
            session_description="Test session for HedValueVector",
            identifier="test_hedvaluevector",
            session_start_time=datetime.now(tzlocal()),
        )

    def tearDown(self):
        """Clean up test file."""
        remove_test_file(self.path)

    def test_roundtrip_write_read(self):
        """Test writing and reading HedValueVector to/from NWB file."""
        # Create test data
        values = HedValueVector(
            name="test_data",
            description="Test value vector for roundtrip",
            data=["red", "green", "blue"],
            hed="Experimental-stimulus, Parameter-value/#",
        )

        # Create table with HedValueVector
        table = DynamicTable(name="value_table", description="Table containing HedValueVector", columns=[values])

        # Add to NWB file
        self.nwbfile.add_analysis(table)

        # Write to file
        with NWBHDF5IO(self.path, mode="w") as io:
            io.write(self.nwbfile)

        # Read from file
        with NWBHDF5IO(self.path, mode="r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            read_table = read_nwbfile.analysis["value_table"]
            read_values = read_table["test_data"]

            # Verify data integrity
            self.assertIsInstance(read_values, HedValueVector)
            self.assertEqual(read_values.name, "test_data")
            self.assertEqual(list(read_values.data), ["red", "green", "blue"])
            self.assertEqual(read_values.hed, "Experimental-stimulus, Parameter-value/#")
