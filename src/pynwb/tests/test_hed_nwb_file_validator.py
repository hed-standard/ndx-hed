"""
Unit tests for HedNWBValidator validate_file method.
"""

import unittest
import tempfile
import os
from datetime import datetime
from dateutil.tz import tzlocal
from pynwb import NWBFile, ProcessingModule, NWBHDF5IO
from pynwb.core import DynamicTable, VectorData
from ndx_events import EventsTable, TimestampVectorData
from ndx_hed import HedTags, HedLabMetaData, HedValueVector
from ndx_hed.utils.hed_nwb_validator import HedNWBValidator
from hed.errors import ErrorHandler


class TestHedNWBFileValidator(unittest.TestCase):
    """Test class for HedNWBValidator validate_file method."""

    def setUp(self):
        """Set up test data for file validation."""

        # Create HED lab metadata with a basic schema
        self.hed_metadata = HedLabMetaData(hed_schema_version="8.4.0")

        # Create HedNWBValidator instance
        self.validator = HedNWBValidator(self.hed_metadata)

        # Create reusable test tables (but don't add to files yet)
        self.valid_hed_tags = HedTags(data=["Sensory-event", "Visual-presentation", "Agent-action"])

        self.invalid_hed_tags = HedTags(data=["InvalidTag123", "NonExistentEvent", "BadTag/WithSlash"])

        # Create test tables
        self.valid_table = DynamicTable(
            name="valid_events",
            description="Table with valid HED tags",
            columns=[
                VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0]),
                self.valid_hed_tags,
            ],
        )

        self.invalid_table = DynamicTable(
            name="invalid_events",
            description="Table with invalid HED tags",
            columns=[
                VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0]),
                self.invalid_hed_tags,
            ],
        )

        self.no_hed_table = DynamicTable(
            name="no_hed_events",
            description="Table without HED tags",
            columns=[
                VectorData(name="event_time", description="Event times", data=[1.0, 2.0, 3.0]),
                VectorData(name="event_type", description="Event types", data=["A", "B", "C"]),
            ],
        )

        # Create EventsTable with proper structure
        timestamp_data = TimestampVectorData(name="timestamp", description="Event timestamps", data=[1.0, 2.0, 3.0])

        hed_data = HedTags(
            name="HED", description="HED annotations", data=["Sensory-event", "Agent-action", "InvalidEventTag"]
        )

        self.events_table = EventsTable(
            name="test_events_table", description="EventsTable with HED annotations", columns=[timestamp_data, hed_data]
        )

    def _create_nwbfile_with_hed_metadata(self, identifier="test_file"):
        """Helper method to create NWB file with HED metadata."""
        nwbfile = NWBFile(
            session_description="Test session with HED metadata",
            identifier=identifier,
            session_start_time=datetime.now(tzlocal()),
        )
        nwbfile.add_lab_meta_data(self.hed_metadata)
        return nwbfile

    def _create_nwbfile_without_hed_metadata(self, identifier="test_file_no_hed"):
        """Helper method to create NWB file without HED metadata."""
        return NWBFile(
            session_description="Test session without HED metadata",
            identifier=identifier,
            session_start_time=datetime.now(tzlocal()),
        )

    def test_validate_file_with_hed_metadata_and_valid_table(self):
        """Test validate_file with NWB file containing HED metadata and valid table."""
        # Create NWB file with HED metadata and add valid table
        nwbfile = self._create_nwbfile_with_hed_metadata("valid_table_test")
        nwbfile.add_acquisition(self.valid_table)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # For valid HED tags, there should be no validation errors
        error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
        self.assertEqual(len(error_issues), 0, f"Unexpected errors with valid HED tags: {error_issues}")

    def test_validate_file_without_hed_metadata(self):
        """Test validate_file with NWB file without HED metadata."""
        # Create NWB file without HED metadata and add a table
        nwbfile = self._create_nwbfile_without_hed_metadata("no_hed_test")
        nwbfile.add_acquisition(self.valid_table)

        # Should raise HedFileError for missing schema
        with self.assertRaises(Exception) as cm:
            self.validator.validate_file(nwbfile)

        # Check that it's the expected schema error
        self.assertIn("does not have a valid HED schema", str(cm.exception))

    def test_validate_file_with_invalid_hed_tags(self):
        """Test validate_file with NWB file containing invalid HED tags."""
        # Create NWB file with HED metadata and add invalid table
        nwbfile = self._create_nwbfile_with_hed_metadata("invalid_tags_test")
        nwbfile.add_acquisition(self.invalid_table)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list with validation issues
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Should find validation issues for invalid HED tags")

        # Should contain error-level issues for invalid tags (severity 1 = error)
        error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
        self.assertGreater(len(error_issues), 0, "Should find validation errors for invalid HED tags")

        # Check that the specific invalid tags are flagged
        invalid_tag_codes = [issue["code"] for issue in error_issues]
        self.assertIn("TAG_INVALID", invalid_tag_codes, "Should find TAG_INVALID errors")

    def test_validate_file_with_mixed_tables(self):
        """Test validate_file with NWB file containing multiple tables."""
        # Create NWB file and add multiple tables
        nwbfile = self._create_nwbfile_with_hed_metadata("mixed_tables_test")
        nwbfile.add_acquisition(self.valid_table)
        nwbfile.add_acquisition(self.invalid_table)
        nwbfile.add_acquisition(self.no_hed_table)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should contain issues from the invalid table only
        if issues:
            # Should have validation errors from invalid table
            error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
            self.assertGreater(len(error_issues), 0, "Should find errors from invalid table")

    def test_validate_file_with_events_table(self):
        """Test validate_file with NWB file containing EventsTable."""
        # Create NWB file and add EventsTable
        nwbfile = self._create_nwbfile_with_hed_metadata("events_table_test")
        nwbfile.add_acquisition(self.events_table)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should handle EventsTable appropriately (calls validate_events)
        # May have issues due to invalid tag in the EventsTable
        if issues:
            # Check that issues are validation-related, not schema-related
            schema_issues = [issue for issue in issues if "schema" in issue.get("message", "").lower()]
            # Should not have schema issues since HED metadata is present
            self.assertEqual(len(schema_issues), 0, "Should not have schema errors with proper HED metadata")

    def test_validate_file_with_trials_table(self):
        """Test validate_file with NWB file containing trials table with HED."""
        # Create NWB file with HED metadata
        nwbfile = self._create_nwbfile_with_hed_metadata("trials_test")

        # Add HED column to trials table
        nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")

        # Add some trials with HED annotations (mix of valid and invalid)
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Sensory-event")  # Valid

        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="InvalidTrialTag")  # Invalid

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should validate the trials table and find issues with invalid tag
        error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
        self.assertGreater(len(error_issues), 0, "Should find validation errors for invalid trial HED tag")

    def test_validate_file_invalid_input(self):
        """Test validate_file with invalid input."""
        # Test with None
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_file(None)
        self.assertIn("not a valid NWBFile instance", str(cm.exception))

        # Test with non-NWBFile object
        with self.assertRaises(ValueError) as cm:
            self.validator.validate_file("not_an_nwbfile")
        self.assertIn("not a valid NWBFile instance", str(cm.exception))

    def test_validate_file_with_error_handler(self):
        """Test validate_file with custom error handler."""
        # Create NWB file with issues
        nwbfile = self._create_nwbfile_with_hed_metadata("error_handler_test")
        nwbfile.add_acquisition(self.invalid_table)

        # Create custom error handler
        error_handler = ErrorHandler(check_for_warnings=True)

        # Validate with custom error handler
        issues = self.validator.validate_file(nwbfile, error_handler)

        # Should return a list
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0, "Should find validation issues with custom error handler")

    def test_validate_file_empty_file(self):
        """Test validate_file with empty NWB file (no tables)."""
        # Create file with HED metadata but no tables
        nwbfile = self._create_nwbfile_with_hed_metadata("empty_file_test")

        # Validate the empty file
        issues = self.validator.validate_file(nwbfile)

        # Should return empty list (no tables to validate)
        self.assertIsInstance(issues, list)
        self.assertEqual(len(issues), 0, "Empty file should have no validation issues")

    def test_validate_file_nested_tables(self):
        """Test validate_file finds tables in processing modules."""
        # Create NWB file with HED metadata
        nwbfile = self._create_nwbfile_with_hed_metadata("nested_tables_test")

        # Create processing module with tables
        processing_module = ProcessingModule(name="test_processing", description="Test processing module")

        # Add table to processing module
        processing_module.add(self.valid_table)

        # Add processing module to NWB file
        nwbfile.add_processing_module(processing_module)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list and find the nested table
        self.assertIsInstance(issues, list)

        # Should not have errors for valid HED tags in nested table
        error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
        self.assertEqual(len(error_issues), 0, f"Unexpected errors in nested table: {error_issues}")

    def test_validate_file_schema_version_mismatch(self):
        """Test that validate_file handles schema version mismatch correctly."""
        # Create file with different HED metadata
        different_hed_metadata = HedLabMetaData(
            hed_schema_version="8.2.0"  # Different from validator's 8.3.0
        )

        nwbfile = NWBFile(
            session_description="Test with different HED version",
            identifier="schema_mismatch_test",
            session_start_time=datetime.now(tzlocal()),
        )

        nwbfile.add_lab_meta_data(different_hed_metadata)
        nwbfile.add_acquisition(self.valid_table)

        # Should raise HedFileError for schema version mismatch
        with self.assertRaises(Exception) as cm:
            self.validator.validate_file(nwbfile)

        # Check that it's the expected schema version error
        self.assertIn("does not match validator schema version", str(cm.exception))

    def test_validate_file_with_hed_value_vector(self):
        """Test validate_file with HedValueVector columns."""
        # Create table with HedValueVector
        hed_value_vector = HedValueVector(
            name="stimulus_contrast",
            description="Stimulus contrast with HED annotation",
            data=[0.5, 0.7, 0.3],
            hed="Sensory-event, Visual-presentation, Luminance-contrast/#",
        )

        table_with_value_vector = DynamicTable(
            name="stimulus_table",
            description="Table with HedValueVector",
            columns=[VectorData(name="trial_id", description="Trial IDs", data=[1, 2, 3]), hed_value_vector],
        )

        # Create NWB file and add table
        nwbfile = self._create_nwbfile_with_hed_metadata("hed_value_vector_test")
        nwbfile.add_acquisition(table_with_value_vector)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should not have validation errors for valid HED tags in HedValueVector
        error_issues = [issue for issue in issues if issue.get("severity", 0) == 1]
        self.assertEqual(len(error_issues), 0, f"Unexpected errors with HedValueVector: {error_issues}")

    def test_validate_file_multiple_acquisition_objects(self):
        """Test validate_file with multiple acquisition objects of different types."""
        # Create NWB file with HED metadata
        nwbfile = self._create_nwbfile_with_hed_metadata("multiple_objects_test")

        # Add various objects to acquisition
        nwbfile.add_acquisition(self.valid_table)
        nwbfile.add_acquisition(self.events_table)

        # Add a non-DynamicTable object (should be ignored by validator)
        from pynwb.base import TimeSeries
        import numpy as np

        time_series = TimeSeries(
            name="test_timeseries",
            description="Test time series",
            data=np.random.randn(100),
            timestamps=np.arange(100),
            unit="volts",
        )
        nwbfile.add_acquisition(time_series)

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should validate tables but ignore non-table objects
        # May have issues from EventsTable's invalid tag
        if issues:
            # Verify issues are from HED validation, not other errors
            for issue in issues:
                self.assertIsInstance(issue, dict, "Issues should be dictionaries")

    def test_validate_file_complex_nested_structure(self):
        """Test validate_file with complex nested structure including analysis containers."""
        # Create NWB file with HED metadata
        nwbfile = self._create_nwbfile_with_hed_metadata("complex_structure_test")

        # Add table to acquisition
        nwbfile.add_acquisition(self.valid_table)

        # Add processing module with multiple containers
        proc_module = ProcessingModule(name="complex_processing", description="Complex processing with nested tables")

        # Add EventsTable to processing module
        proc_module.add(self.events_table)
        nwbfile.add_processing_module(proc_module)

        # Add trials with HED
        nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Agent-action")

        # Validate the file
        issues = self.validator.validate_file(nwbfile)

        # Should return a list
        self.assertIsInstance(issues, list)

        # Should find all tables in the complex structure
        # May have validation issues from EventsTable's invalid tag

    def test_validate_file_roundtrip_consistency(self):
        """Test that validation results are consistent after writing and reading back the file.

        This is an important test to ensure that:
        1. HED metadata and annotations are properly preserved during file I/O
        2. The validation results are reproducible and consistent
        3. There are no serialization/deserialization issues affecting HED validation
        4. The validator works correctly with files loaded from disk (real-world scenario)
        """
        # Create NWB file with HED metadata and mixed tables (valid and invalid)
        nwbfile = self._create_nwbfile_with_hed_metadata("roundtrip_test")

        # Add tables with both valid and invalid HED tags to ensure we have validation issues
        nwbfile.add_acquisition(self.valid_table)
        nwbfile.add_acquisition(self.invalid_table)

        # Add trials with HED
        nwbfile.add_trial_column(name="HED", col_cls=HedTags, data=[], description="HED annotations for trials")
        nwbfile.add_trial(start_time=0.0, stop_time=1.0, HED="Sensory-event")  # Valid
        nwbfile.add_trial(start_time=2.0, stop_time=3.0, HED="InvalidRoundtripTag")  # Invalid

        # Validate the original file
        original_issues = self.validator.validate_file(nwbfile)

        # Write the file to disk and read it back
        with tempfile.NamedTemporaryFile(suffix=".nwb", delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Write the file
            with NWBHDF5IO(temp_filename, "w") as io:
                io.write(nwbfile)

            # Read the file back
            with NWBHDF5IO(temp_filename, "r") as io:
                read_nwbfile = io.read()

                # Validate the read file
                read_issues = self.validator.validate_file(read_nwbfile)

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        # Compare the validation results
        self.assertIsInstance(original_issues, list, "Original validation should return a list")
        self.assertIsInstance(read_issues, list, "Read file validation should return a list")

        # Should have the same number of issues
        self.assertEqual(
            len(original_issues),
            len(read_issues),
            f"Number of issues should be the same: original={len(original_issues)}, " f"read={len(read_issues)}",
        )

        # Should have issues (since we included invalid HED tags)
        self.assertGreater(len(original_issues), 0, "Should find validation issues in original file")
        self.assertGreater(len(read_issues), 0, "Should find validation issues in read file")

        # Compare issue codes and messages (order might differ, so we'll compare sets)
        original_issue_signatures = set()
        read_issue_signatures = set()

        for issue in original_issues:
            # Create a signature from code, message, and context info
            signature = (
                issue.get("code", ""),
                issue.get("message", ""),
                issue.get("ec_column", ""),
                issue.get("ec_row", ""),
            )
            original_issue_signatures.add(signature)

        for issue in read_issues:
            signature = (
                issue.get("code", ""),
                issue.get("message", ""),
                issue.get("ec_column", ""),
                issue.get("ec_row", ""),
            )
            read_issue_signatures.add(signature)

        # The sets of issue signatures should be identical
        self.assertEqual(
            original_issue_signatures,
            read_issue_signatures,
            "Validation issues should be identical after file roundtrip",
        )

        # Verify we have both error types we expect
        error_codes = [issue.get("code", "") for issue in original_issues]
        self.assertIn("TAG_INVALID", error_codes, "Should find TAG_INVALID errors")

        # Check for specific invalid tags we included
        error_messages = [issue.get("message", "") for issue in original_issues]
        invalid_tag_found = any("InvalidTag123" in msg or "InvalidRoundtripTag" in msg for msg in error_messages)
        self.assertTrue(invalid_tag_found, "Should find our specific invalid tags in error messages")


if __name__ == "__main__":
    unittest.main()
