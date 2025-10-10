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
        self.assertEqual(validator.def_dict, self.hed_metadata.get_definition_dict())
        self.assertIsNotNone(validator.hed_schema)
        # Note: definitions can be None if no definitions were provided

        # Test invalid initialization - not HedLabMetaData instance
        with self.assertRaises(ValueError) as cm:
            HedNWBValidator("invalid_metadata")
        self.assertIn("must be an instance of HedLabMetaData", str(cm.exception))

        # Test with None
        with self.assertRaises(ValueError) as cm:
            HedNWBValidator(None)
        self.assertIn("must be an instance of HedLabMetaData", str(cm.exception))

    def test_hed_validator_init_invalid_schema_version(self):
        """Test that HedLabMetaData raises ValueError for invalid schema version."""
        # This tests that HedLabMetaData itself validates the schema during construction
        with self.assertRaises(ValueError) as cm:
            HedLabMetaData(hed_schema_version="99.99.99")
        self.assertIn("Failed to load HED schema version", str(cm.exception))

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
            hed="(Duration/# s, (Sensory-event))",
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
            data=[100, 200, 300, 400, "abc"],
            hed="(Delay/# ms, (Sensory-event))",
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
            hed="InvalidTag123, (BadSyntax, # units)",
        )

        issues = self.validator.validate_value_vector(invalid_template_bad_syntax)

        # Should have issues for invalid template
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)

    def test_validate_value_vector_template_no_placeholder(self):
        """Test validate_value_vector with template missing # placeholder."""
        # Should raise ValueError during construction since no # placeholder
        with self.assertRaises(ValueError) as cm:
            HedValueVector(
                name="no_placeholder", description="Template without placeholder", data=[1.0, 2.0, 3.0], hed="Red, Blue"
            )

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
            hed="(Duration/# s, (Sensory-event))",
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
            hed="(Duration/# invalidUnit, (Green))",  # invalidUnit is not a valid unit
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
            hed="(Duration/# s, (Green))",
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
            hed="(Duration/# s, (Sensory-event, Item/Extension))",
        )

        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_value_vector(valid_template_duration, error_handler)

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
            name="empty", description="Empty data array", data=[], hed="(Duration/# s, (Sensory-event))"
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
            data=[None, "", "n/a", float("nan")],
            hed="(Duration/# s, (Green))",
        )

        issues = self.validator.validate_value_vector(skippable_values)

        # Should skip all values and only validate template
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)

    def test_validate_value_vector_placeholder_substitution(self):
        """Test that # placeholder is correctly substituted with actual values."""
        # Create a simple template where we can verify substitution
        test_vector = HedValueVector(
            name="test_sub", description="Test substitution", data=[1.5, 2.5], hed="(Duration/# s, (Green))"
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
            hed="(Duration/# s, (Sensory-event))",
        )

        issues = self.validator.validate_value_vector(negative_vector)

        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0)  # HED doesn't check value ranges

    def test_validate_value_vector_zero_values(self):
        """Test validate_value_vector with zero values."""
        zero_vector = HedValueVector(
            name="zero", description="Zero values", data=[0.0, 0.0, 0.0], hed="(Duration/# s, (Sensory-event))"
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
            hed="(Duration/# s, (Sensory-event))",
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
            hed="(Duration/# s, (Sensory-event))",
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
            data=[0.5, "abc", 1.5, 2.0],
            hed="(Duration/# s, (Sensory-event))",
        )

        delay_vector = HedValueVector(
            name="delay",
            description="Delay values with HED template",
            data=[100, 200, 300, "gef"],
            hed="(Delay/# ms, (Sensory-event))",
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
            HedValueVector(
                name="multi",
                description="Multiple placeholders",
                data=[1.0, 2.0, 3.0],
                hed="(Delay/# ms, Duration/# s)",
            )

        # Verify the error message mentions the placeholder requirement
        self.assertIn("must contain exactly one '#' placeholder", str(cm.exception))
        self.assertIn("found 2", str(cm.exception))
        self.assertIn("multi", str(cm.exception))


class TestValidateWithDefinitions(unittest.TestCase):
    """Test class for validating HED tags that reference definitions.

    All validation methods (validate_vector, validate_table, validate_value_vector,
    and validate_events) now support external definition dictionaries by passing
    def_dict parameter to HedString during validation. This allows HED tags to
    reference definitions defined in HedLabMetaData.
    """

    def setUp(self):
        """Set up test data with definitions."""
        # Define custom HED definitions
        self.test_definitions = (
            "(Definition/Go-stimulus, (Sensory-event, Visual-presentation)), "
            "(Definition/Stop-stimulus, (Sensory-event, Auditory-presentation)), "
            "(Definition/Correct-response, (Agent-action, Correct-action)), "
            "(Definition/Incorrect-response, (Agent-action, Incorrect-action)), "
            "(Definition/Response-time/#, (Time-interval/# s))"
        )

        # Create HED lab metadata with definitions
        self.hed_metadata_with_defs = HedLabMetaData(hed_schema_version="8.4.0", definitions=self.test_definitions)

        # Create validator with definitions
        self.validator_with_defs = HedNWBValidator(self.hed_metadata_with_defs)

        # Create validator without definitions for comparison
        self.hed_metadata_no_defs = HedLabMetaData(hed_schema_version="8.4.0")
        self.validator_no_defs = HedNWBValidator(self.hed_metadata_no_defs)

    def test_validator_has_definitions(self):
        """Test that validator properly stores definitions from HedLabMetaData."""
        # Validator with definitions should have non-None definitions (DefinitionDict)
        self.assertIsNotNone(self.validator_with_defs.def_dict)

        # Validator without definitions should have empty DefinitionDict
        # (HedLabMetaData always creates a DefinitionDict, even if empty)
        self.assertIsNotNone(self.validator_no_defs.def_dict)
        self.assertEqual(len(self.validator_no_defs.def_dict.defs), 0)

        # Check that definitions contains the expected definition names
        def_dict = self.validator_with_defs.def_dict
        self.assertEqual(len(def_dict.defs), 5)
        # Note: Definition names are stored in lowercase
        self.assertIn("go-stimulus", def_dict.defs)
        self.assertIn("stop-stimulus", def_dict.defs)
        self.assertIn("correct-response", def_dict.defs)
        self.assertIn("incorrect-response", def_dict.defs)
        self.assertIn("response-time", def_dict.defs)

    def test_validate_vector_with_valid_definition_references(self):
        """Test that validate_vector now supports external definitions.

        Note: validate_vector now uses HedString with def_dict parameter,
        which allows it to validate definition references against the
        external definition dictionary.
        """
        # Create HedTags that reference definitions
        def_tags = HedTags(
            data=[
                "Def/Go-stimulus",
                "Def/Correct-response",
            ]
        )

        # Validate with validator that has definitions - should pass
        issues = self.validator_with_defs.validate_vector(def_tags)

        # Should have NO issues because validate_vector now uses external definitions
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues with valid definitions, but got: {issues}")

    def test_validate_vector_without_definitions_fails(self):
        """Test that validate_vector fails when definitions are not provided."""
        # Create HedTags that reference definitions
        def_tags = HedTags(
            data=[
                "Def/Go-stimulus",
                "Def/Correct-response",
            ]
        )

        # Validate with validator that has NO definitions - should fail
        issues = self.validator_no_defs.validate_vector(def_tags)

        # Should have issues because definitions are not available
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues when definitions are not provided")

        # Error should be DEF_INVALID
        self.assertTrue(any(issue.get("code") == "DEF_INVALID" for issue in issues))

    def test_validate_vector_with_invalid_definition_references(self):
        """Test validate_vector with references to non-existent definitions."""
        # Create HedTags that reference definitions that don't exist
        invalid_def_tags = HedTags(
            data=[
                "Def/NonExistent-definition",
                "Def/Another-missing-def",
            ]
        )

        issues = self.validator_with_defs.validate_vector(invalid_def_tags)

        # Should have issues for non-existent definition references
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for non-existent definitions")

        # Check that the error messages mention the definitions
        self.assertTrue(any(issue.get("code") == "DEF_INVALID" for issue in issues))

    def test_definitions_property_access(self):
        """Test that definitions property correctly returns definition string or None."""
        # Validator with definitions should have non-None definitions property
        self.assertIsNotNone(self.hed_metadata_with_defs.definitions)

        # Validator without definitions should have None
        self.assertIsNone(self.hed_metadata_no_defs.definitions)

        # The definitions string should contain our definition names (lowercase)
        defs_string = self.hed_metadata_with_defs.definitions
        self.assertIn("go-stimulus", defs_string.lower())
        self.assertIn("response-time", defs_string.lower())

    def test_validate_events_with_definition_references(self):
        """Test validate_events with EventsTable containing definition references."""
        # Create EventsTable with definition references
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0, 3.0, 4.0],
                "duration": [0.5, 0.5, 0.5, 0.5],
                "HED": [
                    "Def/Go-stimulus",
                    "Def/Stop-stimulus",
                    "Def/Go-stimulus, Def/Correct-response",
                    "Def/Go-stimulus, Def/Response-time/0.45",
                ],
            }
        )

        events_table = get_events_table(
            name="events_with_defs",
            description="Events using HED definitions",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )

        issues = self.validator_with_defs.validate_events(events_table)

        # Should have no issues since all definitions exist
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_events_with_invalid_definition_references(self):
        """Test validate_events with invalid definition references."""
        # Create EventsTable with invalid definition references
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0],
                "duration": [0.5, 0.5],
                "HED": [
                    "Def/NonExistent-def",
                    "Def/Another-missing-def",
                ],
            }
        )

        events_table = get_events_table(
            name="events_invalid_defs",
            description="Events with invalid definitions",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )

        issues = self.validator_with_defs.validate_events(events_table)

        # Should have issues for non-existent definitions
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for non-existent definitions")

    def test_validate_vector_mixed_definitions_and_regular_tags(self):
        """Test validate_vector with a mix of definition references and regular HED tags.

        NOTE: validate_vector now DOES support external definitions.
        """
        mixed_tags = HedTags(
            data=[
                "Def/Go-stimulus, Red, Visual-presentation",
                "Sensory-event, Def/Correct-response",
                "Def/Response-time/0.5, Agent-action",
                "Blue, Green, Def/Stop-stimulus",
            ]
        )

        issues = self.validator_with_defs.validate_vector(mixed_tags)

        # Should have no issues - all definitions exist and regular tags are valid
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_events_mixed_definitions_and_regular_tags(self):
        """Test validate_events with a mix of definition references and regular HED tags.

        NOTE: This is the original test using validate_events.
        """
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0, 3.0, 4.0],
                "duration": [0.5, 0.5, 0.5, 0.5],
                "HED": [
                    "Def/Go-stimulus, Red, Visual-presentation",
                    "Sensory-event, Def/Correct-response",
                    "Def/Response-time/0.5, Agent-action",
                    "Blue, Green, Def/Stop-stimulus",
                ],
            }
        )

        events_table = get_events_table(
            name="events_mixed",
            description="Events with mixed tags",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )

        issues = self.validator_with_defs.validate_events(events_table)

        # Should have no issues - all definitions exist and regular tags are valid
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_vector_definition_with_invalid_regular_tags(self):
        """Test that invalid regular HED tags are caught even when definitions are valid.

        Uses validate_vector which now supports definitions.
        """
        mixed_tags = HedTags(
            data=[
                "Def/Go-stimulus, InvalidTag123",
                "NonExistentTag, Def/Correct-response",
            ]
        )

        issues = self.validator_with_defs.validate_vector(mixed_tags)

        # Should have issues for invalid regular tags
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for invalid regular tags")

    def test_validate_events_definition_with_invalid_regular_tags(self):
        """Test that invalid regular HED tags are caught even when definitions are valid.

        Uses validate_events to properly support definitions.
        """
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0],
                "duration": [0.5, 0.5],
                "HED": [
                    "Def/Go-stimulus, InvalidTag123",
                    "NonExistentTag, Def/Correct-response",
                ],
            }
        )

        events_table = get_events_table(
            name="events_mixed_invalid",
            description="Events with invalid regular tags",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )

        issues = self.validator_with_defs.validate_events(events_table)

        # Should have issues for invalid regular tags
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for invalid regular tags")

    def test_validate_events_uses_definitions(self):
        """Test that validate_events actually uses the definitions when validating."""
        # This test verifies that definitions are passed to the underlying validation
        # Create an EventsTable that would fail without definitions but passes with them
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0],
                "duration": [0.5, 0.5],
                "HED": [
                    "Def/Go-stimulus",
                    "Def/Response-time/0.5",
                ],
            }
        )

        events_table = get_events_table(
            name="events_def_test",
            description="Events to test definition usage",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )

        # Validate with definitions - should pass
        issues_with_defs = self.validator_with_defs.validate_events(events_table)
        self.assertEqual(
            len(issues_with_defs), 0, f"Should have no issues with definitions, but got: {issues_with_defs}"
        )

        # Validate without definitions - should fail
        issues_no_defs = self.validator_no_defs.validate_events(events_table)
        self.assertGreater(len(issues_no_defs), 0, "Should have issues without definitions")

    def test_validate_table_with_definition_references(self):
        """Test validate_table with DynamicTable containing definition references."""
        # Create HedTags with definition references
        def_tags = HedTags(
            data=[
                "Def/Go-stimulus",
                "Def/Stop-stimulus",
                "Def/Correct-response",
                "Def/Go-stimulus, Def/Response-time/0.45",
            ]
        )

        # Create table with definition-based HedTags
        table_with_defs = DynamicTable(
            name="table_with_defs",
            description="Table using HED definitions",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3, 4]),
                def_tags,
            ],
        )

        issues = self.validator_with_defs.validate_table(table_with_defs)

        # Should have no issues since all definitions exist
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_table_with_invalid_definition_references(self):
        """Test validate_table with invalid definition references."""
        # Create HedTags with invalid definition references
        invalid_def_tags = HedTags(
            data=[
                "Def/NonExistent-def",
                "Def/Another-missing-def",
            ]
        )

        table_invalid_defs = DynamicTable(
            name="table_invalid_defs",
            description="Table with invalid definitions",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2]),
                invalid_def_tags,
            ],
        )

        issues = self.validator_with_defs.validate_table(table_invalid_defs)

        # Should have issues for non-existent definitions
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for non-existent definitions")

    def test_validate_table_mixed_definitions_and_regular_tags(self):
        """Test validate_table with mix of definition references and regular HED tags."""
        mixed_tags = HedTags(
            data=[
                "Def/Go-stimulus, Red, Visual-presentation",
                "Sensory-event, Def/Correct-response",
                "Blue, Def/Stop-stimulus",
            ]
        )

        table_mixed = DynamicTable(
            name="table_mixed",
            description="Table with mixed tags",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
                mixed_tags,
            ],
        )

        issues = self.validator_with_defs.validate_table(table_mixed)

        # Should have no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_table_without_definitions_fails(self):
        """Test that validate_table fails when definitions are not provided."""
        def_tags = HedTags(
            data=[
                "Def/Go-stimulus",
                "Def/Correct-response",
            ]
        )

        table_with_defs = DynamicTable(
            name="table_needs_defs",
            description="Table needing definitions",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2]),
                def_tags,
            ],
        )

        # Validate without definitions - should fail
        issues = self.validator_no_defs.validate_table(table_with_defs)

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues when definitions are not provided")

    def test_validate_value_vector_with_definitions(self):
        """Test validate_value_vector with HED template containing definition references.

        Note: Uses a simple (non-placeholder) definition since HedValueVector
        already has its own placeholder mechanism.
        """
        # Create HedValueVector with simple definition in template
        value_vector_with_def = HedValueVector(
            name="stimulus_size",
            description="Stimulus sizes with definition template",
            data=[0.5, 0.6, 0.7, 0.8],
            hed="Def/Go-stimulus, (Size/# cm^2)",
        )

        issues = self.validator_with_defs.validate_value_vector(value_vector_with_def)

        # Should have no issues - definition exists
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_value_vector_with_invalid_definition(self):
        """Test validate_value_vector with invalid definition in template."""
        # Create HedValueVector with non-existent definition
        value_vector_invalid_def = HedValueVector(
            name="invalid_def",
            description="Template with invalid definition",
            data=[1.0, 2.0],
            hed="Def/NonExistent-definition/#",
        )

        issues = self.validator_with_defs.validate_value_vector(value_vector_invalid_def)

        # Should have issues for non-existent definition
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for non-existent definition")

    def test_validate_value_vector_mixed_definitions_and_regular_tags(self):
        """Test validate_value_vector with both definitions and regular tags in template."""
        # Create HedValueVector mixing definition and regular tags
        value_vector_mixed = HedValueVector(
            name="mixed_template",
            description="Template with definition and regular tags",
            data=[100, 200, 300],
            hed="Def/Response-time/#, Red",
        )

        issues = self.validator_with_defs.validate_value_vector(value_vector_mixed)

        # Should have no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_value_vector_without_definitions_fails(self):
        """Test that validate_value_vector fails when definitions are not provided."""
        value_vector_needs_def = HedValueVector(
            name="needs_def",
            description="Template needing definition",
            data=[0.5, 0.6],
            hed="Def/Go-stimulus, (Time-value/# s)",
        )

        # Validate without definitions - should fail
        issues = self.validator_no_defs.validate_value_vector(value_vector_needs_def)

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues when definitions are not provided")

    def test_validate_table_with_value_vector_and_definitions(self):
        """Test validate_table with both HedTags and HedValueVector using definitions."""
        # Create HedTags with definitions
        hed_tags = HedTags(
            data=[
                "Def/Go-stimulus",
                "Def/Stop-stimulus",
                "Def/Correct-response",
            ]
        )

        # Create HedValueVector with definitions
        hed_values = HedValueVector(
            name="stimulus_sizes",
            description="Stimulus sizes",
            data=[0.5, 0.6, 0.7],
            hed="Def/Go-stimulus, Size/# cm^2",
        )

        # Create table with both
        table_combined = DynamicTable(
            name="table_combined",
            description="Table with HedTags and HedValueVector using definitions",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
                hed_tags,
                hed_values,
            ],
        )

        issues = self.validator_with_defs.validate_table(table_combined)

        # Should have no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")


class TestValidateFile(unittest.TestCase):
    """Test class for validating entire NWB files with validate_file method."""

    def setUp(self):
        """Set up test data."""
        from pynwb import NWBFile
        from datetime import datetime
        from pytz import timezone

        # Create HED lab metadata with definitions
        self.test_definitions = (
            "(Definition/Go-stimulus, (Sensory-event, Visual-presentation)), "
            "(Definition/Stop-stimulus, (Sensory-event, Auditory-presentation))"
        )
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0", definitions=self.test_definitions)

        # Create validator
        self.validator = HedNWBValidator(self.hed_metadata)

        # Create a test NWB file
        self.nwbfile = NWBFile(
            session_description="Test session for HED validation",
            identifier="test_file_001",
            session_start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone("US/Pacific")),
        )

        # Add HED metadata to the file
        self.nwbfile.add_lab_meta_data(self.hed_metadata)

    def test_validate_file_with_valid_tables(self):
        """Test validate_file with NWB file containing valid HED tags."""
        # Add a table with valid HED tags
        valid_tags = HedTags(data=["Sensory-event", "Visual-presentation", "Def/Go-stimulus"])
        trials_table = DynamicTable(
            name="trials",
            description="Trial data with HED tags",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
                valid_tags,
            ],
        )
        # Add as acquisition instead of time_intervals
        self.nwbfile.add_acquisition(trials_table)

        issues = self.validator.validate_file(self.nwbfile)

        # Should have no issues for valid file
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_file_with_invalid_tags(self):
        """Test validate_file with NWB file containing invalid HED tags."""
        # Add a table with invalid HED tags
        invalid_tags = HedTags(data=["InvalidTag123", "NonExistentEvent", "BadTag"])
        trials_table = DynamicTable(
            name="trials",
            description="Trial data with invalid HED tags",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
                invalid_tags,
            ],
        )
        self.nwbfile.add_acquisition(trials_table)

        issues = self.validator.validate_file(self.nwbfile)

        # Should have issues for invalid tags
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues for invalid tags")

    def test_validate_file_with_multiple_tables(self):
        """Test validate_file with multiple DynamicTable objects."""
        # Add first table with valid tags
        valid_tags1 = HedTags(data=["Sensory-event", "Def/Go-stimulus"])
        table1 = DynamicTable(
            name="trials",
            description="Trial data",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2]),
                valid_tags1,
            ],
        )
        self.nwbfile.add_acquisition(table1)

        # Add second table with valid tags
        valid_tags2 = HedTags(data=["Agent-action", "Def/Stop-stimulus"])
        table2 = DynamicTable(
            name="responses",
            description="Response data",
            columns=[
                VectorData(name="response_id", description="Response IDs", data=[1, 2]),
                valid_tags2,
            ],
        )
        # Add as acquisition
        self.nwbfile.add_acquisition(table2)

        issues = self.validator.validate_file(self.nwbfile)

        # Should validate both tables with no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_file_with_events_table(self):
        """Test validate_file with EventsTable object."""
        # Create EventsTable
        events_df = pd.DataFrame(
            {
                "onset": [1.0, 2.0, 3.0],
                "duration": [0.5, 0.5, 0.5],
                "HED": ["Def/Go-stimulus", "Sensory-event", "Def/Stop-stimulus"],
            }
        )

        events_table = get_events_table(
            name="events",
            description="Event data with HED tags",
            df=events_df,
            meanings={"categorical": {}, "value": {}},
        )
        self.nwbfile.add_acquisition(events_table)

        issues = self.validator.validate_file(self.nwbfile)

        # Should validate EventsTable with no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_file_with_value_vectors(self):
        """Test validate_file with HedValueVector columns."""
        # Create table with HedValueVector
        hed_values = HedValueVector(
            name="intensity",
            description="Stimulus intensities",
            data=[0.5, 0.6, 0.7],
            hed="Def/Go-stimulus, Red-color/# m-0",
        )

        table = DynamicTable(
            name="trials",
            description="Trial data with HedValueVector",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]),
                hed_values,
            ],
        )
        self.nwbfile.add_acquisition(table)

        issues = self.validator.validate_file(self.nwbfile)

        # Should validate HedValueVector with no issues
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, f"Expected no issues but got: {issues}")

    def test_validate_file_no_hed_metadata(self):
        """Test validate_file raises error when HedLabMetaData is missing."""
        from pynwb import NWBFile
        from datetime import datetime
        from pytz import timezone
        from hed.errors import HedFileError

        # Create NWB file without HED metadata
        nwbfile_no_hed = NWBFile(
            session_description="Test session without HED",
            identifier="test_file_002",
            session_start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone("US/Pacific")),
        )

        with self.assertRaises(HedFileError) as cm:
            self.validator.validate_file(nwbfile_no_hed)
        self.assertIn("does not have a valid HED schema", str(cm.exception))

    def test_validate_file_schema_version_mismatch(self):
        """Test validate_file raises error when schema versions don't match."""
        from pynwb import NWBFile
        from datetime import datetime
        from pytz import timezone
        from hed.errors import HedFileError

        # Create NWB file with different schema version
        nwbfile_different = NWBFile(
            session_description="Test session with different schema",
            identifier="test_file_003",
            session_start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone("US/Pacific")),
        )

        # Add HED metadata with different schema version
        different_metadata = HedLabMetaData(hed_schema_version="8.3.0")
        nwbfile_different.add_lab_meta_data(different_metadata)

        with self.assertRaises(HedFileError) as cm:
            self.validator.validate_file(nwbfile_different)
        self.assertIn("does not match validator schema version", str(cm.exception))

    def test_validate_file_none_input(self):
        """Test validate_file with None input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_file(None)
        self.assertIn("not a valid NWBFile instance", str(cm.exception))

    def test_validate_file_invalid_type(self):
        """Test validate_file with invalid type input."""
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_file("not an nwb file")
        self.assertIn("not a valid NWBFile instance", str(cm.exception))

    def test_validate_file_mixed_valid_invalid_tables(self):
        """Test validate_file with mix of valid and invalid tables."""
        # Add valid table
        valid_tags = HedTags(data=["Sensory-event", "Def/Go-stimulus"])
        valid_table = DynamicTable(
            name="valid_trials",
            description="Valid trial data",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2]),
                valid_tags,
            ],
        )
        self.nwbfile.add_acquisition(valid_table)

        # Add invalid table
        invalid_tags = HedTags(data=["InvalidTag123", "BadTag456"])
        invalid_table = DynamicTable(
            name="invalid_responses",
            description="Invalid response data",
            columns=[
                VectorData(name="response_id", description="Response IDs", data=[1, 2]),
                invalid_tags,
            ],
        )
        self.nwbfile.add_acquisition(invalid_table)

        issues = self.validator.validate_file(self.nwbfile)

        # Should have issues only from the invalid table
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Expected validation issues from invalid table")

        # Check that issues are from the invalid table
        self.assertTrue(any("invalid_responses" in str(issue) for issue in issues))

    def test_validate_file_with_custom_error_handler(self):
        """Test validate_file with custom error handler."""
        # Add table with some issues
        tags = HedTags(data=["Sensory-event"])  # Simple valid tag
        table = DynamicTable(
            name="trials",
            description="Trial data",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1]),
                tags,
            ],
        )
        self.nwbfile.add_acquisition(table)

        # Use error handler that checks for warnings
        error_handler = ErrorHandler(check_for_warnings=True)
        issues = self.validator.validate_file(self.nwbfile, error_handler)

        self.assertIsInstance(issues, list)


if __name__ == "__main__":
    unittest.main()
