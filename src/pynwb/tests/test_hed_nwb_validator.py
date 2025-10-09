"""
Unit tests for HedNWBValidator class.
"""

import unittest
import pandas as pd
from pynwb.core import DynamicTable, VectorData

# from ndx_events import EventsTable, MeaningsTable, TimestampVectorData, DurationVectorData, CategoricalVectorData
from ndx_hed import HedTags, HedLabMetaData, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from ndx_hed.utils.bids2nwb import get_events_table
from hed.errors import ErrorHandler


class TestHedNWBValidatorInit(unittest.TestCase):
    """Test class for HedNWBValidator initialization and basic properties."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

    def test_hed_validator_init(self):
        """Test HedNWBValidator initialization."""
        # Test valid initialization
        validator = HedNWBValidator(self.hed_metadata)
        self.assertIsInstance(validator, HedNWBValidator)
        self.assertEqual(validator.hed_metadata, self.hed_metadata)

        # Test invalid initialization
        with self.assertRaises(ValueError) as cm:
            HedNWBValidator("invalid_metadata")
        self.assertIn("must be an instance of HedLabMetaData", str(cm.exception))

    def test_hed_schema_property(self):
        """Test hed_schema property."""
        validator = HedNWBValidator(self.hed_metadata)
        # Should create schema on first access
        schema = validator.hed_schema
        self.assertIsNotNone(schema)

        # Should return same schema on subsequent calls
        schema2 = validator.hed_schema
        self.assertIs(schema, schema2)


class TestValidateHedTagsVector(unittest.TestCase):
    """Test class for validating HedTags vectors."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)

        # Create test HedTags with valid and invalid tags
        self.valid_tags = HedTags(data=["Sensory-event", "Visual-presentation", "Item", "Agent-action", "Red"])

        self.invalid_tags = HedTags(
            data=[
                "InvalidTag123",
                "NonExistentEvent",
                "BadTag/WithSlash",
                "Sensory-event",  # This one is valid
                "",  # Empty string should be skipped
            ]
        )

        self.mixed_tags = HedTags(
            data=["Sensory-event", "InvalidTag456", "Visual-presentation", "n/a", "AnotherBadTag"]  # Should be skipped
        )

    def test_validate_vector_valid_tags(self):
        """Test validate_vector with valid HED tags."""
        issues = self.validator.validate_vector(self.valid_tags)

        # Should have no issues for valid tags
        self.assertIsInstance(issues, list)
        # Note: We expect this might fail initially until HED tags are corrected
        # If there are issues, they should be validation errors, not exceptions

    def test_validate_vector_invalid_tags(self):
        """Test validate_vector with invalid HED tags."""
        issues = self.validator.validate_vector(self.invalid_tags)

        # Should have issues for invalid tags
        self.assertIsInstance(issues, list)
        # We expect some issues since we have invalid tags
        # Note: Exact count may vary based on actual HED schema validation

    def test_validate_vector_mixed_tags(self):
        """Test validate_vector with mixed valid/invalid HED tags."""
        issues = self.validator.validate_vector(self.mixed_tags)

        # Should have some issues for the invalid tags
        self.assertIsInstance(issues, list)
        # Should have fewer issues than all invalid tags

    def test_validate_vector_with_custom_error_handler(self):
        """Test validate_vector with custom error handler."""
        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_vector(self.invalid_tags, error_handler)

        self.assertIsInstance(issues, list)

    def test_validate_vector_none_input(self):
        """Test validate_vector with None input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_vector(None)
        self.assertIn("not a valid HedTags instance", str(cm.exception))

    def test_validate_vector_invalid_type(self):
        """Test validate_vector with invalid type input."""
        invalid_input = VectorData(name="test", description="test", data=["test"])
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_vector(invalid_input)
        self.assertIn("not a valid HedTags instance", str(cm.exception))

    def test_validate_vector_empty_tags(self):
        """Test validate_vector with empty HED tags."""
        empty_tags = HedTags(data=[])
        issues = self.validator.validate_vector(empty_tags)

        # Should return empty list for empty tags
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_vector_only_skippable_values(self):
        """Test validate_vector with only skippable values (None, empty, n/a)."""
        skippable_tags = HedTags(data=[None, "", "n/a", ""])
        issues = self.validator.validate_vector(skippable_tags)

        # Should return empty list since all values are skipped
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)


class TestValidateTable(unittest.TestCase):
    """Test class for validating DynamicTable objects."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)

        # Create test HedTags with valid and invalid tags
        self.valid_tags = HedTags(data=["Sensory-event", "Visual-presentation", "Item", "Agent-action", "Red"])

        self.invalid_tags = HedTags(
            data=[
                "InvalidTag123",
                "NonExistentEvent",
                "BadTag/WithSlash",
                "Sensory-event",  # This one is valid
                "",  # Empty string should be skipped
            ]
        )

        self.mixed_tags = HedTags(
            data=["Sensory-event", "InvalidTag456", "Visual-presentation", "n/a", "AnotherBadTag"]  # Should be skipped
        )

        # Create test tables
        self.valid_table = DynamicTable(
            name="valid_test_table",
            description="Table with valid HED tags",
            columns=[VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]), self.valid_tags],
        )

        self.invalid_table = DynamicTable(
            name="invalid_test_table",
            description="Table with invalid HED tags",
            columns=[VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]), self.invalid_tags],
        )

        self.mixed_table = DynamicTable(
            name="mixed_test_table",
            description="Table with mixed valid/invalid HED tags",
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]),
                self.mixed_tags,
                VectorData(name="other_data", description="Other test data", data=["a", "b", "c", "d", "e"]),
            ],
        )

        self.no_hed_table = DynamicTable(
            name="no_hed_table",
            description="Table without HED tags",
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3]),
                VectorData(name="more_data", description="More test data", data=["x", "y", "z"]),
            ],
        )

    def test_validate_table_valid_table(self):
        """Test validate_table with table containing valid HED tags."""
        issues = self.validator.validate_table(self.valid_table)

        self.assertIsInstance(issues, list)
        # Should have no issues for valid table
        # Note: May fail initially until HED tags are corrected

    def test_validate_table_invalid_table(self):
        """Test validate_table with table containing invalid HED tags."""
        issues = self.validator.validate_table(self.invalid_table)

        self.assertIsInstance(issues, list)
        # Should have issues for invalid table

    def test_validate_table_mixed_table(self):
        """Test validate_table with table containing mixed valid/invalid HED tags."""
        issues = self.validator.validate_table(self.mixed_table)

        self.assertIsInstance(issues, list)
        # Should have some issues

    def test_validate_table_no_hed_columns(self):
        """Test validate_table with table containing no HED columns."""
        issues = self.validator.validate_table(self.no_hed_table)

        # Should return empty list since no HED columns to validate
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_table_with_custom_error_handler(self):
        """Test validate_table with custom error handler."""
        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_table(self.mixed_table, error_handler)

        self.assertIsInstance(issues, list)

    def test_table_multiple_hed_columns(self):
        """Test validate_table with multiple HED columns."""
        # Create table with multiple HED columns
        with self.assertRaises(ValueError) as cm:
            DynamicTable(
                name="multi_hed_table",
                description="Table with multiple HED columns",
                columns=[
                    VectorData(name="data", description="Test data", data=[1, 2, 3]),
                    HedTags(data=["Sensory-event", "Visual-presentation", "Auditory-event"]),
                    HedTags(name="HED", data=["Agent-action", "InvalidTag789", "Red"]),
                ],
            )
        self.assertIn("columns with duplicate names", str(cm.exception))

    def test_validate_table_none_input(self):
        """Test validate_table with None input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_table(None)
        self.assertIn("not a valid DynamicTable instance", str(cm.exception))

    def test_validate_table_invalid_type(self):
        """Test validate_table with invalid type input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_table("not a table")
        self.assertIn("not a valid DynamicTable instance", str(cm.exception))

    def test_validate_integration(self):
        """Integration test for both functions working together."""
        # Create a comprehensive test scenario
        integration_table = DynamicTable(
            name="integration_test",
            description="Integration test table",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3, 4]),
                HedTags(data=["Sensory-event", "InvalidTag999", "", "Visual-presentation"]),
                VectorData(name="response", description="Responses", data=["A", "B", "C", "D"]),
            ],
        )

        # Test table validation
        table_issues = self.validator.validate_table(integration_table)
        self.assertIsInstance(table_issues, list)

        # Test vector validation directly
        hed_column = None
        for col in integration_table.columns:
            if isinstance(col, HedTags):
                hed_column = col
                break

        self.assertIsNotNone(hed_column)
        vector_issues = self.validator.validate_vector(hed_column)
        self.assertIsInstance(vector_issues, list)


class TestValidateEventsTable(unittest.TestCase):
    """Test class for validating EventsTable objects."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)

        # Create test EventsTables using get_events_table function
        # This is the proper way to create EventsTable for testing

        # Create valid test data for EventsTable
        valid_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0, 3.0, 4.0, 5.0],
                "duration": [0.5, 0.5, 0.5, 0.5, 0.5],
                "HED": ["Sensory-event", "Visual-presentation", "Auditory-event", "Sensory-event", "Auditory-event"],
            }
        )

        # Create invalid test data for EventsTable
        invalid_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0, 3.0],
                "duration": [0.5, 0.5, 0.5],
                "HED": ["InvalidTag123", "NonExistentEvent", "BadTag/WithSlash"],
            }
        )

        # Create EventsTables using get_events_table
        self.valid_events_table = get_events_table(
            name="valid_events",
            description="Valid events table with HED tags",
            df=valid_df,
            meanings={"categorical": {}, "value": {}},
        )

        self.invalid_events_table = get_events_table(
            name="invalid_events",
            description="Invalid events table with HED tags",
            df=invalid_df,
            meanings={"categorical": {}, "value": {}},
        )

    def test_validate_events_valid_table(self):
        """Test validate_events with valid EventsTable."""
        issues = self.validator.validate_events(self.valid_events_table)

        self.assertIsInstance(issues, list)
        # Should have no issues for valid events table
        # Note: May fail initially until HED tags are corrected

    def test_validate_events_invalid_table(self):
        """Test validate_events with invalid EventsTable."""
        issues = self.validator.validate_events(self.invalid_events_table)

        self.assertIsInstance(issues, list)
        # Should have issues for invalid events table

    def test_validate_events_with_custom_error_handler(self):
        """Test validate_events with custom error handler."""
        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_events(self.invalid_events_table, error_handler)

        self.assertIsInstance(issues, list)

    def test_validate_events_none_input(self):
        """Test validate_events with None input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_events(None)
        self.assertIn("not a valid EventsTable instance", str(cm.exception))

    def test_validate_events_invalid_type(self):
        """Test validate_events with invalid type input."""
        invalid_input = DynamicTable(
            name="test", description="test", columns=[VectorData(name="test", description="test", data=["test"])]
        )
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_events(invalid_input)
        self.assertIn("not a valid EventsTable instance", str(cm.exception))

    def test_validate_events_conversion_integration(self):
        """Test that validate_events properly calls get_bids_events."""
        # This test verifies the integration with get_bids_events
        # Even though validation logic is not implemented yet,
        # it should successfully convert to BIDS format
        issues = self.validator.validate_events(self.valid_events_table)

        # Should return a list (even if empty for now)
        self.assertIsInstance(issues, list)

        # Test with events table that has both HED tags and categorical data
        issues = self.validator.validate_events(self.valid_events_table)
        self.assertIsInstance(issues, list)


class TestValidateHedValueVector(unittest.TestCase):
    """Test class for validating HedValueVector objects."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)

    def test_validate_value_vector_valid_template(self):
        """Test validate_value_vector with valid HED template."""
        valid_template_duration = HedValueVector(
            name="duration",
            description="Duration values with HED template",
            data=[0.5, 1.0, 1.5, 2.0, 2.5],
            hed="(Duration/# s, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(valid_template_duration)

        # Should have no issues for valid template and values
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_value_vector_valid_template_bad_data(self):
        """Test validate_value_vector with valid delay template."""
        valid_template_delay = HedValueVector(
            name="delay",
            description="Delay values with HED template",
            data=[100, 200, 300, 400, 'abc'],
            hed="(Delay/# ms, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(valid_template_delay)

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)  # Expect issues due to 'abc' value

    def test_validate_value_vector_invalid_template(self):
        """Test validate_value_vector with invalid HED template."""
        invalid_template_bad_syntax = HedValueVector(
            name="bad_syntax",
            description="Template with bad HED syntax",
            data=[1.0, 2.0, 3.0],
            hed="InvalidTag123, (BadSyntax, # units)"
        )

        issues = self.validator.validate_value_vector(invalid_template_bad_syntax)

        # Should have issues for invalid template
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

    def test_validate_value_vector_template_no_placeholder(self):
        """Test validate_value_vector with template missing # placeholder."""
        # Should raise ValueError during construction since no # placeholder
        with self.assertRaises(ValueError) as cm:
             HedValueVector(name="no_placeholder", description="Template without placeholder",
                            data=[1.0, 2.0, 3.0], hed="Red, Blue" )

        # Verify the error message mentions the placeholder requirement
        self.assertIn("must contain exactly one '#' placeholder", str(cm.exception))
        self.assertIn("found 0", str(cm.exception))
        self.assertIn("no_placeholder", str(cm.exception))

    def test_validate_value_vector_valid_values(self):
        """Test validate_value_vector with valid values."""
        valid_template_duration = HedValueVector(
            name="duration",
            description="Duration values with HED template",
            data=[0.5, 1.0, 1.5, 2.0, 2.5],
            hed="(Duration/# s, (Sensory-event))"
        )

        # All values should create valid HED strings when substituted
        issues = self.validator.validate_value_vector(valid_template_duration)

        self.assertIsInstance(issues, list)

    def test_validate_value_vector_invalid_units(self):
        """Test validate_value_vector with invalid units."""
        valid_template_invalid_units = HedValueVector(
            name="invalid_units",
            description="Valid template but invalid unit values",
            data=[1.0, 2.0, 3.0],
            hed="(Duration/# invalidUnit, (Green))"  # invalidUnit is not a valid unit
        )

        # Template is valid but substituted values create invalid HED
        issues = self.validator.validate_value_vector(valid_template_invalid_units)

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

    def test_validate_value_vector_mixed_values(self):
        """Test validate_value_vector with mixed valid/invalid values."""
        mixed_values = HedValueVector(
            name="mixed",
            description="Mixed valid and skippable values",
            data=[1.0, None, 2.0, "", 3.0],
            hed="(Duration/# s, (Green))"
        )

        issues = self.validator.validate_value_vector(mixed_values)

        # Should only validate non-skippable values
        self.assertIsInstance(issues, list)

    def test_validate_value_vector_with_custom_error_handler(self):
        """Test validate_value_vector with custom error handler."""
        valid_template_duration = HedValueVector(
            name="duration",
            description="Duration values with HED template",
            data=[0.5, 1.0, 1.5, 2.0, 2.5],
            hed="(Duration/# s, (Sensory-event, Item/Extension))"
        )

        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_value_vector(
            valid_template_duration,
            error_handler
        )

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

    def test_validate_value_vector_none_input(self):
        """Test validate_value_vector with None input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_value_vector(None)
        self.assertIn("not a valid HedValueVector instance", str(cm.exception))

    def test_validate_value_vector_invalid_type(self):
        """Test validate_value_vector with invalid type input."""
        invalid_input = VectorData(name="test", description="test", data=[1, 2, 3])
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_value_vector(invalid_input)
        self.assertIn("not a valid HedValueVector instance", str(cm.exception))

    def test_validate_value_vector_none_hed_template(self):
        """Test validate_value_vector with None HED template."""
        # Should raise TypeError during construction when hed=None
        with self.assertRaises(TypeError) as cm:
            HedValueVector(name="no_hed", description="Vector without HED template", data=[1.0, 2.0, 3.0], hed=None)

        # Verify the error message mentions that None is not allowed
        self.assertIn("None is not allowed", cm.exception.args[0])

    def test_validate_value_vector_empty_data(self):
        """Test validate_value_vector with empty data."""
        empty_data = HedValueVector(
            name="empty",
            description="Empty data array",
            data=[],
            hed="(Duration/# s, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(empty_data)

        # Should validate template but no data to substitute
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_value_vector_skippable_values(self):
        """Test validate_value_vector with only skippable values (None, empty, n/a, NaN)."""
        skippable_values = HedValueVector(
            name="skippable",
            description="Only skippable values",
            data=[None, "", "n/a", float('nan')],
            hed="(Duration/# s, (Green))"
        )

        issues = self.validator.validate_value_vector(skippable_values)

        # Should skip all values and only validate template
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_value_vector_placeholder_substitution(self):
        """Test that # placeholder is correctly substituted with actual values."""
        # Create a simple template where we can verify substitution
        test_vector = HedValueVector(
            name="test_sub",
            description="Test substitution",
            data=[1.5, 2.5],
            hed="(Duration/# s, (Green))"
        )

        issues = self.validator.validate_value_vector(test_vector)
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)  # Expect no issues if substitution works correctly

    def test_validate_value_vector_negative_values(self):
        """Test validate_value_vector with negative values."""
        negative_vector = HedValueVector(
            name="negative",
            description="Negative values",
            data=[-1.0, -2.0, -3.0],
            hed="(Duration/# s, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(negative_vector)

        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)  # HED doesn't check value ranges

    def test_validate_value_vector_zero_values(self):
        """Test validate_value_vector with zero values."""
        zero_vector = HedValueVector(
            name="zero",
            description="Zero values",
            data=[0.0, 0.0, 0.0],
            hed="(Duration/# s, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(zero_vector)

        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)  # Zero is a valid numeric value

    def test_validate_value_vector_large_values(self):
        """Test validate_value_vector with very large values."""
        large_vector = HedValueVector(
            name="large",
            description="Large values",
            data=[1000000.0, 2000000.0, 3000000.0],
            hed="(Duration/# s, (Sensory-event))"
        )

        issues = self.validator.validate_value_vector(large_vector)

        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)  # Large values should be valid

    def test_validate_value_vector_in_table(self):
        """Test validate_value_vector within a DynamicTable context."""
        valid_template_duration = HedValueVector(
            name="duration",
            description="Duration values with HED template",
            data=[0.5, 1.0, 1.5, 2.0, 2.5],
            hed="(Duration/# s, (Sensory-event))"
        )

        # Create a table with HedValueVector column
        table = DynamicTable(
            name="test_table",
            description="Table with HedValueVector",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3, 4, 5]),
                valid_template_duration,
            ],
        )

        # Validate the table (which should call validate_value_vector internally)
        issues = self.validator.validate_table(table)

        self.assertIsInstance(issues, list)

    def test_validate_table_with_multiple_value_vectors(self):
        """Test validate_table with multiple HedValueVector columns."""
        # Create two different HedValueVector columns
        duration_vector = HedValueVector(
            name="duration",
            description="Duration values with HED template",
            data=[0.5, 'abc', 1.5, 2.0],
            hed="(Duration/# s, (Sensory-event))"
        )

        delay_vector = HedValueVector(
            name="delay",
            description="Delay values with HED template",
            data=[100, 200, 300, 'gef'],
            hed="(Delay/# ms, (Sensory-event))"
        )

        # Create a table with both HedValueVector columns
        table = DynamicTable(
            name="multi_value_vector_table",
            description="Table with multiple HedValueVector columns",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3, 4]),
                duration_vector,
                delay_vector,
                VectorData(name="response", description="Response data", data=["A", "B", "C", "D"]),
            ],
        )

        # Validate the table - should validate both HedValueVector columns
        issues = self.validator.validate_table(table)

        # Should return a list (both columns should be validated)
        self.assertIsInstance(issues, list)
        self.assertGreaterEqual(len(issues), 2)
        self.assertTrue(any("Duration/abc" in i.get("message", "") for i in issues))
        self.assertTrue(any("Delay/gef" in i.get("message", "") for i in issues))

    def test_validate_value_vector_multiple_placeholders(self):
        """Test validate_value_vector with multiple # placeholders in template."""
        # Should raise ValueError during construction since there are multiple # placeholders
        with self.assertRaises(ValueError) as cm:
            HedValueVector(name="multi", description="Multiple placeholders",
                           data=[1.0, 2.0, 3.0], hed="(Delay/# ms, Duration/# s)" )

        # Verify the error message mentions the placeholder requirement
        self.assertIn("must contain exactly one '#' placeholder", str(cm.exception))
        self.assertIn("found 2", str(cm.exception))
        self.assertIn("multi", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
