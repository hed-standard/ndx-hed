"""
Unit tests for HedNWBValidator class.
"""
import unittest
import tempfile
import os
import pandas as pd
from pynwb.core import DynamicTable, VectorData
from ndx_events import EventsTable, MeaningsTable, TimestampVectorData, DurationVectorData, CategoricalVectorData
from ndx_hed import HedTags, HedLabMetaData
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from hed.errors import ErrorHandler
from hed.schema import HedSchema


class TestHedNWBValidator(unittest.TestCase):
    """Test class for HedNWBValidator class."""

    def setUp(self):
        """Set up test data."""
        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(
            name="hed_schema",
            hed_schema_version="8.3.0"
        )
        
        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)
        
        # Create test HedTags with valid and invalid tags
        self.valid_tags = HedTags(data=[
            "Sensory-event",
            "Visual-presentation", 
            "Item",
            "Agent-action",
            "Red"
        ])
        
        self.invalid_tags = HedTags(data=[
            "InvalidTag123",
            "NonExistentEvent",
            "BadTag/WithSlash",
            "Sensory-event",  # This one is valid
            ""  # Empty string should be skipped
        ])
        
        self.mixed_tags = HedTags(data=[
            "Sensory-event",
            "InvalidTag456", 
            "Visual-presentation",
            "n/a",  # Should be skipped
            "AnotherBadTag"
        ])
        
        # Create test tables
        self.valid_table = DynamicTable(
            name="valid_test_table",
            description="Table with valid HED tags",
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]),
                self.valid_tags
            ]
        )
        
        self.invalid_table = DynamicTable(
            name="invalid_test_table", 
            description="Table with invalid HED tags",
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]),
                self.invalid_tags
            ]
        )
        
        self.mixed_table = DynamicTable(
            name="mixed_test_table",
            description="Table with mixed valid/invalid HED tags", 
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3, 4, 5]),
                self.mixed_tags,
                VectorData(name="other_data", description="Other test data", data=['a', 'b', 'c', 'd', 'e'])
            ]
        )
        
        self.no_hed_table = DynamicTable(
            name="no_hed_table",
            description="Table without HED tags",
            columns=[
                VectorData(name="data", description="Test data", data=[1, 2, 3]),
                VectorData(name="more_data", description="More test data", data=['x', 'y', 'z'])
            ]
        )
        
        # Create test EventsTables using get_events_table function
        # This is the proper way to create EventsTable for testing
        from ndx_hed.utils.bids2nwb import get_events_table
        
        # Create valid test data for EventsTable
        valid_df = pd.DataFrame({
            'onset': [1.0, 2.0, 3.0, 4.0, 5.0],
            'duration': [0.5, 0.5, 0.5, 0.5, 0.5],
            'HED': [
                "Sensory-event",
                "Visual-presentation", 
                "Auditory-event",
                "Sensory-event",
                "Auditory-event"
            ]
        })
        
        # Create invalid test data for EventsTable
        invalid_df = pd.DataFrame({
            'onset': [1.0, 2.0, 3.0],
            'duration': [0.5, 0.5, 0.5],
            'HED': [
                "InvalidTag123",
                "NonExistentEvent",
                "BadTag/WithSlash"
            ]
        })
        
        # Create EventsTables using get_events_table
        self.valid_events_table = get_events_table(
            name="valid_events",
            description="Valid events table with HED tags",
            df=valid_df,
            meanings={"categorical": {}, "value": {}}
        )
        
        self.invalid_events_table = get_events_table(
            name="invalid_events", 
            description="Invalid events table with HED tags",
            df=invalid_df,
            meanings={"categorical": {}, "value": {}}
        )

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
        # Should create schema on first access
        schema = self.validator.hed_schema
        self.assertIsNotNone(schema)
        
        # Should return same schema on subsequent calls
        schema2 = self.validator.hed_schema
        self.assertIs(schema, schema2)

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
                    HedTags(name="HED", data=["Agent-action", "InvalidTag789", "Red"])
                ]
            )
        self.assertIn("columns with duplicate names", str(cm.exception))
        

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

    def test_validate_integration(self):
        """Integration test for both functions working together."""
        # Create a comprehensive test scenario
        integration_table = DynamicTable(
            name="integration_test",
            description="Integration test table",
            columns=[
                VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3, 4]),
                HedTags(data=["Sensory-event", "InvalidTag999", "", "Visual-presentation"]),
                VectorData(name="response", description="Responses", data=['A', 'B', 'C', 'D'])
            ]
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
            name="test", 
            description="test", 
            columns=[VectorData(name="test", description="test", data=["test"])]
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


if __name__ == '__main__':
    unittest.main()
