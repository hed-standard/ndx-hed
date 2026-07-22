"""
Unit tests for bids2nwb utility functions.
"""

import unittest
import os
import json
import pandas as pd
from hed.schema import load_schema_version
from hed.models import DefinitionDict
from pynwb.event import EventsTable, TimestampVectorData, DurationVectorData
from hdmf.common import MeaningsTable
from ndx_hed import HedTags, HedValueVector
from pynwb.core import DynamicTable, VectorData
from ndx_hed.utils.bids2nwb import (
    extract_meanings,
    get_categorical_meanings,
    get_events_table,
    get_bids_tabular,
    extract_definitions,
)


class TestExtractMeanings(unittest.TestCase):
    """Test class for extract_meanings function."""

    def setUp(self):
        """Set up test data."""
        # Sample sidecar data for testing
        self.sample_sidecar_data = {
            "event_type": {
                "Levels": {
                    "left_click": "Participant pushes the left button.",
                    "right_click": "Participant pushes the right button",
                    "show_cross": "Display an image of a cross character on the screen.",
                },
                "HED": {
                    "left_click": "Agent-action, Participant-response, (Press, (Push-button, (Left-side-of)))",
                    "right_click": "Agent-action, Participant-response, (Press, (Push-button, (Right-side-of)))",
                    "show_cross": "Sensory-event, Visual-presentation, (Cross, (Center-of, Computer-screen))",
                },
            },
            "trial": {"Description": "Number of the trial in the experiment", "HED": "Experimental-trial/#"},
            "letter": {"Description": "The character appearing on the screen", "HED": "(Character, Parameter-value/#)"},
            "simple_categorical": {"Levels": {"A": "Letter A", "B": "Letter B"}},
        }

        # Path to actual test data file
        current_dir = os.path.dirname(__file__)
        data_dir = os.path.join(current_dir, "data")
        self.json_path = os.path.join(data_dir, "task-WorkingMemory_events.json")

    def test_extract_meanings_basic(self):
        """Test extract_meanings with sample data."""
        result = extract_meanings(self.sample_sidecar_data)

        # Check structure
        self.assertIn("categorical", result)
        self.assertIn("value", result)
        self.assertIsInstance(result["categorical"], dict)
        self.assertIsInstance(result["value"], dict)

        # Check categorical data (extract_meanings now keeps the raw sidecar column-info dict;
        # the MeaningsTable is built later in get_events_table once the target column exists)
        self.assertIn("event_type", result["categorical"])
        self.assertIn("simple_categorical", result["categorical"])
        self.assertIsInstance(result["categorical"]["event_type"], dict)
        self.assertIn("Levels", result["categorical"]["event_type"])

        # Check value data
        self.assertIn("trial", result["value"])
        self.assertIn("letter", result["value"])
        self.assertEqual(result["value"]["trial"], "Experimental-trial/#")
        self.assertEqual(result["value"]["letter"], "(Character, Parameter-value/#)")

    def test_extract_meanings_real_data(self):
        """Test extract_meanings with real sidecar data if available."""
        if not os.path.exists(self.json_path):
            self.skipTest("Real sidecar data file not found")

        # Load the real sidecar data
        with open(self.json_path, "r") as f:
            real_sidecar_data = json.load(f)

        result = extract_meanings(real_sidecar_data)

        # Check structure
        self.assertIn("categorical", result)
        self.assertIn("value", result)

        # Test specific categorical columns from the real data (raw sidecar dicts now)
        expected_categorical = ["event_type", "task_role"]
        for col_name in expected_categorical:
            self.assertIn(col_name, result["categorical"])
            self.assertIsInstance(result["categorical"][col_name], dict)

        # Test event_type categorical column in detail
        event_type_info = result["categorical"]["event_type"]
        self.assertIn("Levels", event_type_info)
        self.assertIn("HED", event_type_info)

        # Check event_type has the expected levels
        expected_events = [
            "left_click",
            "right_click",
            "show_cross",
            "show_dash",
            "show_letter",
            "sound_beep",
            "sound_buzz",
        ]
        actual_events = list(event_type_info["Levels"].keys())
        for event in expected_events:
            self.assertIn(event, actual_events)

        # Test task_role categorical column
        task_role_info = result["categorical"]["task_role"]
        expected_task_roles = [
            "bad_trial",
            "feedback_correct",
            "feedback_incorrect",
            "fixate",
            "ignored_correct",
            "to_remember",
            "work_memory",
        ]
        actual_task_roles = list(task_role_info["Levels"].keys())
        for role in expected_task_roles:
            self.assertIn(role, actual_task_roles)

        # Test specific value columns from the real data
        expected_value_columns = ["trial", "letter", "memory_cond"]
        for col_name in expected_value_columns:
            self.assertIn(col_name, result["value"])
            self.assertIsInstance(result["value"][col_name], str)

        # Test specific HED strings
        self.assertEqual(result["value"]["trial"], "Experimental-trial/#")
        self.assertEqual(result["value"]["letter"], "(Character, Parameter-value/#)")
        self.assertEqual(
            result["value"]["memory_cond"],
            "(Condition-variable/Items-to-memorize, Item-count, Target, Parameter-value/#)",
        )

        # Test that non-HED column (sample) is not included
        self.assertNotIn("sample", result["categorical"])
        self.assertNotIn("sample", result["value"])

        # Test that we have the expected number of columns
        self.assertEqual(len(result["categorical"]), 2)  # event_type, task_role
        self.assertEqual(len(result["value"]), 3)  # trial, letter, memory_cond

        # Test HED strings in categorical data (from the raw sidecar HED dict)
        event_hed_data = list(event_type_info["HED"].values())
        self.assertIn("Agent-action, Participant-response, (Press, (Push-button, (Left-side-of)))", event_hed_data)
        self.assertIn("Sensory-event, Visual-presentation, (Cross, (Center-of, Computer-screen))", event_hed_data)
        self.assertIn("Sensory-event, Auditory-presentation, Beep", event_hed_data)

    def test_extract_meanings_empty_input(self):
        """Test extract_meanings with empty input."""
        result = extract_meanings({})

        self.assertEqual(result["categorical"], {})
        self.assertEqual(result["value"], {})

    def test_extract_meanings_mixed_column_types(self):
        """Test extract_meanings correctly categorizes different column types."""
        mixed_data = {
            "categorical_with_hed": {"Levels": {"A": "Letter A"}, "HED": {"A": "Character"}},
            "categorical_without_hed": {"Levels": {"B": "Letter B"}},
            "value_column": {"HED": "Simple/#"},
            "no_hed_column": {"Description": "Just a description"},
        }

        result = extract_meanings(mixed_data)

        # Check categorical columns
        self.assertIn("categorical_with_hed", result["categorical"])
        self.assertIn("categorical_without_hed", result["categorical"])

        # Check value columns
        self.assertIn("value_column", result["value"])

        # Non-HED column should not appear in either
        self.assertNotIn("no_hed_column", result["categorical"])
        self.assertNotIn("no_hed_column", result["value"])


class TestExtractDefinitions(unittest.TestCase):
    """Test class for extract_definitions function."""

    def setUp(self):
        """Set up test data."""
        # Sample sidecar data with definitions
        self.sample_sidecar_with_definitions = {
            "event_type": {
                "Levels": {
                    "face_stimulus": "A face stimulus appears on screen",
                    "house_stimulus": "A house stimulus appears on screen",
                },
                "HED": {
                    "face_stimulus": "Sensory-event, (Visual-presentation, Def/Face-image)",
                    "house_stimulus": "Sensory-event, (Visual-presentation, Def/House-image)",
                },
            },
            "response_time": {
                "Description": "Time from stimulus onset to response",
                "Units": "ms",
                "HED": "Parameter-value/#",
            },
            "definitions": {
                "HED": {
                    "defList": "(Definition/Face-image, (Image, Face)),"
                    + "(Definition/House-image, (Image, Building/House)),"
                    + "(Definition/Response-event, (Agent-action, Participant-response))",
                    "defThreeLevel": "(Definition/Three-level/#, (Item, Parameter-value/#))",
                }
            },
        }

        # Sidecar data without {definitions
        self.sample_sidecar_no_definitions = {
            "event_type": {
                "Levels": {
                    "left_click": "Participant pushes the left button",
                    "right_click": "Participant pushes the right button",
                },
                "HED": {
                    "left_click": "Agent-action, Participant-response, (Press, (Push-button, (Left-side-of)))",
                    "right_click": "Agent-action, Participant-response, (Press, (Push-button, (Right-side-of)))",
                },
            }
        }

        # Load a HED schema for testing
        self.hed_schema = load_schema_version("8.4.0")

    def test_extract_definitions_with_definitions(self):
        """Test extract_definitions with sidecar containing definitions."""
        definitions, issues = extract_definitions(self.sample_sidecar_with_definitions, self.hed_schema)

        # Check that definitions is a DefinitionDict
        self.assertIsInstance(definitions, DefinitionDict)

        # Check that issues is a list
        self.assertIsInstance(issues, list)

        # Check specific definitions exist
        def_names = definitions.defs.keys()
        self.assertIn("face-image", def_names)
        self.assertIn("house-image", def_names)
        self.assertIn("response-event", def_names)
        self.assertIn("three-level", def_names)

    def test_extract_definitions_without_definitions(self):
        """Test extract_definitions with sidecar without definitions."""
        definitions, issues = extract_definitions(self.sample_sidecar_no_definitions, self.hed_schema)

        # Check that definitions is a DefinitionDict
        self.assertIsInstance(definitions, DefinitionDict)

        # Check that issues is a list
        self.assertIsInstance(issues, list)

        # Check that no definitions were extracted
        self.assertEqual(len(definitions), 0)

    def test_extract_definitions_with_hed_schema_group(self):
        """Test extract_definitions with HedSchemaGroup."""
        # Create a schema group with library schemas
        library_schema_version = '["score_2.1.0","lang_1.1.0"]'
        hed_schema_group = load_schema_version(library_schema_version)

        definitions, issues = extract_definitions(self.sample_sidecar_with_definitions, hed_schema_group)

        # Check that definitions is a DefinitionDict
        self.assertIsInstance(definitions, DefinitionDict)

        # Check that issues is a list
        self.assertIsInstance(issues, list)

        # Check that function works with HedSchemaGroup
        self.assertGreaterEqual(len(definitions), 0)

    def test_extract_definitions_empty_sidecar(self):
        """Test extract_definitions with empty sidecar."""
        empty_sidecar = {}
        definitions, issues = extract_definitions(empty_sidecar, self.hed_schema)

        # Check that definitions is a DefinitionDict
        self.assertIsInstance(definitions, DefinitionDict)

        # Check that issues is a list
        self.assertIsInstance(issues, list)

        # Check that no definitions were extracted
        self.assertEqual(len(definitions), 0)


class TestGetCategoricalMeanings(unittest.TestCase):
    """Test class for get_categorical_meanings function."""

    def setUp(self):
        """Set up test data."""
        # Sample sidecar data for testing
        self.sample_sidecar_data = {
            "event_type": {
                "Levels": {
                    "left_click": "Participant pushes the left button.",
                    "right_click": "Participant pushes the right button",
                    "show_cross": "Display an image of a cross character on the screen.",
                },
                "HED": {
                    "left_click": "Agent-action, Participant-response, (Press, (Push-button, (Left-side-of)))",
                    "right_click": "Agent-action, Participant-response, (Press, (Push-button, (Right-side-of)))",
                    "show_cross": "Sensory-event, Visual-presentation, (Cross, (Center-of, Computer-screen))",
                },
            },
            "simple_categorical": {"Levels": {"A": "Letter A", "B": "Letter B"}},
        }

    def test_get_categorical_meanings_with_hed(self):
        """Test get_categorical_meanings with HED data."""
        column_info = self.sample_sidecar_data["event_type"]
        target_column = VectorData(name="event_type", description="event type", data=[])

        result = get_categorical_meanings(target_column, column_info)

        # Check result type
        self.assertIsInstance(result, MeaningsTable)

        # Check table properties
        self.assertEqual(result.name, "event_type_meanings")
        self.assertIn("event_type", result.description)

        # Check table has the expected columns
        self.assertIn("value", result.colnames)
        self.assertIn("meaning", result.colnames)
        self.assertIn("HED", result.colnames)

        # Check data content
        df = result.to_dataframe()
        self.assertEqual(len(df), 3)  # Should have 3 rows for the 3 levels

        # Check specific values
        values = df["value"].tolist()
        self.assertIn("left_click", values)
        self.assertIn("right_click", values)
        self.assertIn("show_cross", values)

        # Check HED column type
        self.assertIsInstance(result["HED"], HedTags)

    def test_get_categorical_meanings_without_hed(self):
        """Test get_categorical_meanings without HED data."""
        column_info = self.sample_sidecar_data["simple_categorical"]
        target_column = VectorData(name="simple_categorical", description="simple", data=[])

        result = get_categorical_meanings(target_column, column_info)

        # Check result type
        self.assertIsInstance(result, MeaningsTable)

        # Check table properties
        self.assertEqual(result.name, "simple_categorical_meanings")

        # Should not have HED column
        self.assertNotIn("HED", result.colnames)

        # Check data content
        df = result.to_dataframe()
        self.assertEqual(len(df), 2)  # Should have 2 rows for A and B

    def test_get_categorical_meanings_with_description(self):
        """Test get_categorical_meanings with custom description."""
        column_info = {
            "Description": "Custom description for testing",
            "Levels": {"test1": "Test value 1", "test2": "Test value 2"},
        }
        target_column = VectorData(name="test_column", description="test", data=[])

        result = get_categorical_meanings(target_column, column_info)

        self.assertEqual(result.description, "Custom description for testing")

    def test_get_categorical_meanings_empty_levels(self):
        """Test get_categorical_meanings with empty levels."""
        column_info = {"Description": "Empty levels test"}
        target_column = VectorData(name="empty_column", description="empty", data=[])

        result = get_categorical_meanings(target_column, column_info)

        # Should create empty table
        self.assertIsInstance(result, MeaningsTable)
        df = result.to_dataframe()
        self.assertEqual(len(df), 0)

    def test_get_categorical_meanings_hed_dict_without_levels(self):
        """HED provided as a dict but no Levels: categories come from the HED dict keys."""
        column_info = {
            "HED": {"a": "Sensory-event", "b": "Agent-action"},
        }
        target_column = VectorData(name="cat", description="cat", data=[])

        result = get_categorical_meanings(target_column, column_info)

        # Rows are built from the HED keys (not dropped just because Levels is absent)
        df = result.to_dataframe()
        self.assertEqual(sorted(df["value"].tolist()), ["a", "b"])
        self.assertIn("HED", result.colnames)
        self.assertIsInstance(result["HED"], HedTags)
        hed_by_value = dict(zip(df["value"].tolist(), df["HED"].tolist(), strict=True))
        self.assertEqual(hed_by_value["a"], "Sensory-event")
        self.assertEqual(hed_by_value["b"], "Agent-action")

    def test_get_categorical_meanings_levels_with_string_hed(self):
        """Levels present but HED is a string (a value annotation, not categorical): no HED column,
        and no AttributeError from treating the string as a dict."""
        column_info = {
            "Levels": {"a": "Level A", "b": "Level B"},
            "HED": "Sensory-event, Label/#",  # string, not a per-category dict
        }
        target_column = VectorData(name="cat", description="cat", data=[])

        result = get_categorical_meanings(target_column, column_info)

        df = result.to_dataframe()
        self.assertEqual(sorted(df["value"].tolist()), ["a", "b"])
        # The string HED must not be treated as categorical -> no HED column
        self.assertNotIn("HED", result.colnames)


class TestGetEventsTable(unittest.TestCase):
    """Test class for get_events_table function."""

    def setUp(self):
        """Set up test data."""
        # Sample meanings data (raw sidecar column-info dicts, as produced by extract_meanings)
        self.sample_meanings = {
            "categorical": {
                "event_type": {
                    "Levels": {"show_cross": "Display a cross", "left_click": "Left button press"},
                    "HED": {"show_cross": "Visual-event", "left_click": "Agent-action"},
                }
            },
            "value": {"trial": "Experimental-trial/#", "letter": "(Character, Parameter-value/#)"},
        }

        # Sample DataFrame with typical event data
        self.sample_df = pd.DataFrame({
            "onset": [0.0, 1.5, 3.0],
            "duration": [0.5, 1.0, 0.8],
            "event_type": ["show_cross", "left_click", "show_cross"],
            "trial": [1, 1, 2],
            "letter": ["A", "B", "C"],
            "HED": ["Event-1", "Event-2", "Event-3"],
            "other_column": ["data1", "data2", "data3"],
        })

    def test_get_events_table_basic(self):
        """Test get_events_table with basic data."""
        result = get_events_table(
            name="test_events", description="Test events table", df=self.sample_df, meanings=self.sample_meanings
        )

        # Check result type
        self.assertIsInstance(result, EventsTable)

        # Check table properties
        self.assertEqual(result.name, "test_events")
        self.assertEqual(result.description, "Test events table")

        # Check that all expected columns are present
        expected_columns = {"timestamp", "duration", "event_type", "trial", "letter", "HED", "other_column"}
        actual_columns = set(result.colnames)
        self.assertEqual(actual_columns, expected_columns)

        # Check column types
        self.assertIsInstance(result["timestamp"], TimestampVectorData)
        self.assertIsInstance(result["duration"], DurationVectorData)
        # Categorical columns are now plain VectorData annotated by a MeaningsTable on the table
        self.assertIsInstance(result["event_type"], VectorData)
        self.assertIsInstance(result.meanings_tables.get("event_type_meanings"), MeaningsTable)
        self.assertIsInstance(result["trial"], HedValueVector)
        self.assertIsInstance(result["letter"], HedValueVector)
        self.assertIsInstance(result["HED"], HedTags)
        self.assertIsInstance(result["other_column"], VectorData)

        # Check data integrity
        self.assertEqual(list(result["timestamp"].data), [0.0, 1.5, 3.0])
        self.assertEqual(list(result["duration"].data), [0.5, 1.0, 0.8])
        self.assertEqual(list(result["event_type"].data), ["show_cross", "left_click", "show_cross"])

    def test_get_events_table_with_na_values(self):
        """Test get_events_table with 'n/a' values in onset and duration."""
        df_with_na = pd.DataFrame({
            "onset": [0.0, "n/a", 3.0],
            "duration": ["N/A", 1.0, "na"],
            "event_type": ["A", "B", "C"],
        })

        meanings = {"categorical": {}, "value": {}}

        result = get_events_table(name="na_test", description="Test with n/a values", df=df_with_na, meanings=meanings)

        # Check that n/a values were converted to NaN
        timestamp_data = list(result["timestamp"].data)
        duration_data = list(result["duration"].data)

        self.assertEqual(timestamp_data[0], 0.0)
        self.assertTrue(pd.isna(timestamp_data[1]))
        self.assertEqual(timestamp_data[2], 3.0)

        self.assertTrue(pd.isna(duration_data[0]))
        self.assertEqual(duration_data[1], 1.0)
        self.assertTrue(pd.isna(duration_data[2]))

    def test_get_events_table_minimal_columns(self):
        """Test get_events_table with minimal required columns."""
        minimal_df = pd.DataFrame({"onset": [1.0, 2.0], "duration": [0.5, 0.7]})

        meanings = {"categorical": {}, "value": {}}

        result = get_events_table(name="minimal", description="Minimal events table", df=minimal_df, meanings=meanings)

        # Should have timestamp and duration columns
        self.assertIn("timestamp", result.colnames)
        self.assertIn("duration", result.colnames)
        self.assertEqual(len(result.colnames), 2)

    def test_get_events_table_only_categorical(self):
        """Test get_events_table with only categorical columns."""
        cat_df = pd.DataFrame({"onset": [1.0, 2.0], "event_type": ["A", "B"], "condition": ["cond1", "cond2"]})

        # Create meanings with categorical data (raw sidecar dicts)
        meanings = {
            "categorical": {
                "event_type": {
                    "Levels": {"A": "Event A", "B": "Event B"},
                    "HED": {"A": "EventA-tag", "B": "EventB-tag"},
                },
                "condition": {"Levels": {"cond1": "Condition 1", "cond2": "Condition 2"}},
            },
            "value": {},
        }

        result = get_events_table(
            name="categorical_test", description="Test categorical columns", df=cat_df, meanings=meanings
        )

        # Categorical columns are plain VectorData
        self.assertIsInstance(result["event_type"], VectorData)
        self.assertIsInstance(result["condition"], VectorData)

        # Check that MeaningsTables are properly attached to the table
        event_meanings = result.meanings_tables.get("event_type_meanings")
        cond_meanings = result.meanings_tables.get("condition_meanings")
        self.assertIsInstance(event_meanings, MeaningsTable)
        self.assertIsInstance(cond_meanings, MeaningsTable)
        # event_type has HED, condition does not
        self.assertIn("HED", event_meanings.colnames)
        self.assertNotIn("HED", cond_meanings.colnames)
        # Each MeaningsTable targets its column
        self.assertIs(event_meanings.target, result["event_type"])
        self.assertIs(cond_meanings.target, result["condition"])

    def test_get_events_table_only_value_columns(self):
        """Test get_events_table with only value columns."""
        value_df = pd.DataFrame({"onset": [1.0, 2.0], "trial_num": [1, 2], "response_time": [0.5, 0.8]})

        meanings = {
            "categorical": {},
            "value": {
                "trial_num": "Experimental-trial/#",
                "response_time": "Agent-action, Response-time, Parameter-value/#",
            },
        }

        result = get_events_table(name="value_test", description="Test value columns", df=value_df, meanings=meanings)

        # Check value columns are HedValueVector
        self.assertIsInstance(result["trial_num"], HedValueVector)
        self.assertIsInstance(result["response_time"], HedValueVector)

        # Check HED annotations
        self.assertEqual(result["trial_num"].hed, "Experimental-trial/#")
        self.assertEqual(result["response_time"].hed, "Agent-action, Response-time, Parameter-value/#")

    def test_get_events_table_empty_dataframe(self):
        """Test get_events_table with empty DataFrame."""

        result = get_events_table(
            name="empty_test",
            description="Empty events table",
            df=pd.DataFrame(),
            meanings={"categorical": {}, "value": {}},
        )

        # Should create table with only the required timestamp column
        self.assertIsInstance(result, EventsTable)
        self.assertEqual(len(result.colnames), 1)

    def test_get_events_table_real_data(self):
        """Test get_events_table with real test data if available."""
        # Path to real test data
        current_dir = os.path.dirname(__file__)
        data_dir = os.path.join(current_dir, "data")
        tsv_path = os.path.join(data_dir, "sub-001_ses-01_task-WorkingMemory_run-1_events.tsv")
        json_path = os.path.join(data_dir, "task-WorkingMemory_events.json")

        if not os.path.exists(tsv_path) or not os.path.exists(json_path):
            self.skipTest("Real test data files not found")

        # Load real data
        df = pd.read_csv(tsv_path, sep="\t")
        with open(json_path, "r") as f:
            sidecar_data = json.load(f)

        meanings = extract_meanings(sidecar_data)

        result = get_events_table(name="real_events", description="Real event data", df=df, meanings=meanings)

        # Check result
        self.assertIsInstance(result, EventsTable)
        self.assertGreater(len(result.colnames), 0)

        # Should have timestamp column from onset
        self.assertIn("timestamp", result.colnames)
        self.assertIsInstance(result["timestamp"], TimestampVectorData)

        # Check that data length matches original DataFrame
        for col_name in result.colnames:
            self.assertEqual(len(result[col_name].data), len(df))


class TestGetBidsTabular(unittest.TestCase):
    """Test class for get_bids_tabular function."""

    def setUp(self):
        """Set up test data."""
        # Create sample DataFrame
        sample_df = pd.DataFrame({
            "onset": [0.0, 1.5, 3.0],
            "duration": [0.5, 1.0, 0.8],
            "event_type": ["show_cross", "left_click", "show_cross"],
            "trial": [1, 2, 3],
            "letter": ["A", "B", "C"],
            "HED": ["Event-1", "Event-2", "Event-3"],
        })

        # Create meanings dictionary (raw sidecar dicts; event_type has Levels but no HED)
        meanings = {
            "categorical": {
                "event_type": {"Levels": {"show_cross": "Display a cross", "left_click": "Left button press"}},
            },
            "value": {"trial": "Experimental-trial/#", "letter": "(Character, Parameter-value/#)"},
        }

        # Create EventsTable
        self.events_table = get_events_table(
            name="test_events", description="Test events for conversion", df=sample_df, meanings=meanings
        )

    def test_get_bids_tabular_basic(self):
        """Test basic conversion from EventsTable to BIDS format."""
        df, json_data = get_bids_tabular(self.events_table)

        # Check DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("onset", df.columns)  # Should be renamed from timestamp
        self.assertIn("duration", df.columns)
        self.assertIn("event_type", df.columns)
        self.assertIn("trial", df.columns)
        self.assertIn("letter", df.columns)
        self.assertIn("HED", df.columns)

        # Check data integrity
        self.assertEqual(list(df["onset"]), [0.0, 1.5, 3.0])
        self.assertEqual(list(df["duration"]), [0.5, 1.0, 0.8])
        self.assertEqual(list(df["event_type"]), ["show_cross", "left_click", "show_cross"])

        # Check JSON structure
        self.assertIsInstance(json_data, dict)

        # Check categorical column metadata (event_type)
        self.assertIn("event_type", json_data)
        event_info = json_data["event_type"]
        self.assertIn("Levels", event_info)
        self.assertNotIn("HED", event_info)  # No HED since we didn't add HED column

        # Check levels
        expected_levels = {"show_cross": "Display a cross", "left_click": "Left button press"}
        self.assertEqual(event_info["Levels"], expected_levels)

        # Check value column metadata
        self.assertIn("trial", json_data)
        self.assertIn("letter", json_data)
        self.assertEqual(json_data["trial"]["HED"], "Experimental-trial/#")
        self.assertEqual(json_data["letter"]["HED"], "(Character, Parameter-value/#)")

    def test_get_bids_tabular_minimal(self):
        """Test conversion with minimal EventsTable (only timestamp and duration)."""
        # Create minimal DataFrame
        minimal_df = pd.DataFrame({"onset": [1.0, 2.0], "duration": [0.5, 0.7]})

        minimal_meanings = {"categorical": {}, "value": {}}

        minimal_events = get_events_table(
            name="minimal_events", description="Minimal test events", df=minimal_df, meanings=minimal_meanings
        )

        df, json_data = get_bids_tabular(minimal_events)

        # Check DataFrame
        self.assertEqual(list(df.columns), ["onset", "duration"])
        self.assertEqual(list(df["onset"]), [1.0, 2.0])
        self.assertEqual(list(df["duration"]), [0.5, 0.7])

        # JSON should be empty or minimal since no HED metadata
        self.assertIsInstance(json_data, dict)

    def test_get_bids_tabular_only_categorical(self):
        """Test conversion with only categorical columns."""
        # Create categorical-only data
        cat_df = pd.DataFrame({"onset": [1.0, 2.0], "condition": ["A", "B"], "response": ["correct", "incorrect"]})

        # Create meanings for both categorical columns (raw sidecar dicts)
        meanings = {
            "categorical": {
                "condition": {
                    "Levels": {"A": "Condition A", "B": "Condition B"},
                    "HED": {"A": "Experimental-condition, CondA", "B": "Experimental-condition, CondB"},
                },
                "response": {"Levels": {"correct": "Correct response", "incorrect": "Incorrect response"}},
            },
            "value": {},
        }

        events = get_events_table("cat_events", "Categorical events", cat_df, meanings)
        df, json_data = get_bids_tabular(events)

        # Check that both categorical columns are in JSON
        self.assertIn("condition", json_data)
        self.assertIn("response", json_data)

        # Check condition has HED
        self.assertIn("HED", json_data["condition"])
        condition_hed = json_data["condition"]["HED"]
        self.assertEqual(condition_hed["A"], "Experimental-condition, CondA")
        self.assertEqual(condition_hed["B"], "Experimental-condition, CondB")

        # Check response has levels but no HED (since none was provided)
        self.assertIn("Levels", json_data["response"])
        self.assertNotIn("HED", json_data["response"])

    def test_get_bids_tabular_only_value_columns(self):
        """Test conversion with only value columns (HedValueVector)."""
        value_df = pd.DataFrame({"onset": [1.0, 2.0], "trial_num": [1, 2], "response_time": [0.5, 0.8]})

        meanings = {
            "categorical": {},
            "value": {
                "trial_num": "Experimental-trial/#",
                "response_time": "Agent-action, Response-time, Parameter-value/#",
            },
        }

        events = get_events_table("value_events", "Value events", value_df, meanings)
        df, json_data = get_bids_tabular(events)

        # Check JSON has HED for value columns
        self.assertIn("trial_num", json_data)
        self.assertIn("response_time", json_data)
        self.assertEqual(json_data["trial_num"]["HED"], "Experimental-trial/#")
        self.assertEqual(json_data["response_time"]["HED"], "Agent-action, Response-time, Parameter-value/#")

    def test_get_bids_tabular_roundtrip(self):
        """Test roundtrip conversion: DataFrame/JSON -> EventsTable -> DataFrame/JSON."""
        # Start with original data
        original_df = pd.DataFrame({
            "onset": [0.0, 1.5, 3.0],
            "duration": [0.5, 1.0, 0.8],
            "event_type": ["A", "B", "A"],
            "trial": [1, 2, 3],
        })

        original_json = {
            "event_type": {
                "Description": "Type of event",
                "Levels": {"A": "Event type A", "B": "Event type B"},
                "HED": {"A": "EventA-tag", "B": "EventB-tag"},
            },
            "trial": {"Description": "Trial number", "HED": "Experimental-trial/#"},
        }

        # Convert to EventsTable
        meanings = extract_meanings(original_json)
        events_table = get_events_table("roundtrip_test", "Roundtrip test", original_df, meanings)

        # Convert back to DataFrame/JSON
        converted_df, converted_json = get_bids_tabular(events_table)

        # Check DataFrame roundtrip (with adjustments for expected differences)
        # The converted DataFrame should have "onset" column (renamed from "timestamp")
        self.assertIn("onset", converted_df.columns)
        self.assertNotIn("timestamp", converted_df.columns)

        # Check data content matches (ignoring NaN/"n/a" differences)
        self.assertEqual(list(converted_df["onset"]), list(original_df["onset"]))
        self.assertEqual(list(converted_df["duration"]), list(original_df["duration"]))
        self.assertEqual(list(converted_df["event_type"]), list(original_df["event_type"]))
        self.assertEqual(list(converted_df["trial"]), list(original_df["trial"]))

        # Check column sets match (accounting for timestamp->onset rename)
        original_columns = set(original_df.columns)
        converted_columns = set(converted_df.columns)
        self.assertEqual(original_columns, converted_columns)

        # Check JSON structure (may not be identical due to processing)
        self.assertIn("event_type", converted_json)
        self.assertIn("trial", converted_json)

        # Check key content is preserved
        self.assertEqual(converted_json["trial"]["HED"], "Experimental-trial/#")
        self.assertIn("Levels", converted_json["event_type"])
        self.assertIn("HED", converted_json["event_type"])

    def test_get_bids_tabular_plain_dynamic_table(self):
        """get_bids_tabular works on a plain (non-EventsTable) DynamicTable.

        With no timestamp/onset column the result is a non-timeline table: the HED column carries
        row HED and a HedValueVector column contributes a value template to the sidecar.
        """
        table = DynamicTable(
            name="trials",
            description="A plain table with HED",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2]),
                HedTags(data=["Sensory-event", "Agent-action"]),
                HedValueVector(name="reaction_time", description="RTs", data=[0.5, 0.6], hed="(Duration, # s)"),
            ],
        )
        df, json_data = get_bids_tabular(table)
        # No onset column (not time-anchored)
        self.assertNotIn("onset", df.columns)
        self.assertIn("HED", df.columns)
        self.assertIn("reaction_time", df.columns)
        # The value column's template is exported in the sidecar; the HED column is self-describing
        self.assertEqual(json_data["reaction_time"]["HED"], "(Duration, # s)")


if __name__ == "__main__":
    unittest.main()
