"""
Unit tests for the JSON-case to NWB conversion in ``nwb_case_builder``.

One hand-written case per mapping rule; they need the HED 8.4.0 schema (bundled with hedtools)
and no submodule.
"""

import unittest

from hdmf.common import MeaningsTable
from pynwb.core import DynamicTable
from pynwb.event import EventsTable

from ndx_hed import HedLabMetaData, HedTags, HedValueVector
from ndx_hed.utils.bids2nwb import get_bids_tabular

from .nwb_case_builder import (
    absent_hed_columns,
    build_combo_table,
    build_events_table,
    build_metadata,
    build_nwbfile,
    build_sidecar_table,
    is_definitions_entry,
    is_ragged,
    join_definitions,
    schema_version_string,
    split_definition_entries,
)

DEFS = ["(Definition/Acc/#, (Acceleration/# m-per-s^2, Red))", "(Definition/MyColor, (Label/Pie))"]


class TestRecordLevel(unittest.TestCase):
    def test_schema_version_string(self):
        self.assertEqual(schema_version_string("8.4.0"), "8.4.0")
        self.assertEqual(schema_version_string([" 8.4.0", "score_2.1.0"]), "8.4.0,score_2.1.0")

    def test_join_definitions(self):
        self.assertIsNone(join_definitions(None, []))
        self.assertEqual(
            join_definitions(["(Definition/A, (Red))"], ["(Definition/B, (Blue))"]),
            "(Definition/A, (Red)), (Definition/B, (Blue))",
        )

    def test_build_metadata_with_definitions(self):
        metadata = build_metadata("8.4.0", DEFS)
        self.assertIsInstance(metadata, HedLabMetaData)
        self.assertEqual(sorted(metadata.get_definition_dict().defs), ["acc", "mycolor"])

    def test_build_metadata_rejects_bad_definition(self):
        with self.assertRaises(ValueError):
            build_metadata("8.4.0", DEFS, ["Definition/Blech, (Red)"])


class TestDefinitionEntries(unittest.TestCase):
    def test_is_definitions_entry(self):
        self.assertTrue(is_definitions_entry({"HED": {"def1": "(Definition/Apple, (Blue))"}}))
        self.assertTrue(is_definitions_entry({"HED": {"def1": "Definition/Blech, (Red)"}}))  # malformed still counts
        self.assertFalse(is_definitions_entry({"HED": {"face": "Red, (Definition/X, (Blue))", "ball": "Blue"}}))
        self.assertFalse(is_definitions_entry({"HED": "Label/#"}))
        self.assertFalse(is_definitions_entry({"Description": "no HED"}))

    def test_split_folds_only_absent_entries(self):
        sidecar = {
            "defs": {"HED": {"def1": "(Definition/Apple, (Blue))"}},
            "event_code": {"HED": {"face": "Red"}},
        }
        remaining, definitions = split_definition_entries(sidecar, ["onset", "duration", "HED"])
        self.assertEqual(list(remaining), ["event_code"])
        self.assertEqual(definitions, ["(Definition/Apple, (Blue))"])
        remaining, definitions = split_definition_entries(sidecar, ["onset", "defs", "HED"])
        self.assertEqual(list(remaining), ["defs", "event_code"])
        self.assertEqual(definitions, [])
        remaining, definitions = split_definition_entries(sidecar, None)
        self.assertEqual(list(remaining), ["event_code"])

    def test_absent_hed_columns(self):
        sidecar = {"event_code": {"HED": {"face": "Red"}}, "onset": {"Description": "time"}, "rt": {"HED": "Label/#"}}
        self.assertEqual(absent_hed_columns(sidecar, ["onset", "duration", "event_code", "HED"]), ["rt"])


class TestSidecarTable(unittest.TestCase):
    def test_zero_row_table_round_trips(self):
        sidecar = {
            "event_code": {"HED": {"show": "Red", "ball": "Blue"}},
            "response": {"Description": "Has HED", "HED": "Label/#"},
            "onset": {"Description": "Onset", "Units": "s"},
        }
        table = build_sidecar_table(sidecar)
        self.assertIsInstance(table, DynamicTable)
        self.assertEqual(len(table), 0)
        self.assertIsInstance(table["response"], HedValueVector)
        self.assertIsInstance(table.get_meanings_for_column("event_code"), MeaningsTable)
        df, json_data = get_bids_tabular(table)
        self.assertEqual(len(df), 0)
        self.assertEqual(json_data["event_code"]["HED"], {"show": "Red", "ball": "Blue"})
        self.assertEqual(json_data["response"]["HED"], "Label/#")
        self.assertNotIn("HED", json_data["onset"])

    def test_empty_sidecar_gives_none(self):
        self.assertIsNone(build_sidecar_table({}))

    def test_bad_template_rejected(self):
        with self.assertRaises(ValueError):
            build_sidecar_table({"trial": {"HED": "Def/Acc/#, Label/#"}})


class TestEventsTable(unittest.TestCase):
    def test_onset_header_gives_events_table(self):
        table = build_events_table([["onset", "duration", "HED"], [4.5, 0, "Red"], ["n/a", 1, "n/a"]])
        self.assertIsInstance(table, EventsTable)
        self.assertIsInstance(table["HED"], HedTags)
        df, _ = get_bids_tabular(table)
        self.assertEqual(list(df.columns), ["onset", "duration", "HED"])

    def test_no_onset_header_gives_dynamic_table(self):
        table = build_events_table([["duration", "HED"], [0, "Red"]])
        self.assertIsInstance(table, DynamicTable)
        self.assertNotIsInstance(table, EventsTable)
        self.assertIsInstance(table["HED"], HedTags)

    def test_is_ragged(self):
        self.assertFalse(is_ragged([["onset", "HED"], [1, "Red"]]))
        self.assertTrue(is_ragged([["onset", "duration", "HED"], [1, "Red"]]))

    def test_combo_table_attaches_meanings_and_templates(self):
        sidecar = {"event_code": {"HED": {"face": "Red"}}, "rt": {"HED": "Label/#"}}
        rows = [["onset", "duration", "event_code", "rt", "HED"], [1.0, 0, "face", "fast", "Blue"]]
        table = build_combo_table(sidecar, rows)
        self.assertIsInstance(table, EventsTable)
        self.assertIsInstance(table["rt"], HedValueVector)
        self.assertIsInstance(table.get_meanings_for_column("event_code"), MeaningsTable)
        rows_no_onset = [["event_code", "rt", "HED"], ["face", "fast", "Blue"]]
        table = build_combo_table(sidecar, rows_no_onset)
        self.assertNotIsInstance(table, EventsTable)
        self.assertIsInstance(table["rt"], HedValueVector)
        self.assertIsInstance(table.get_meanings_for_column("event_code"), MeaningsTable)

    def test_build_nwbfile(self):
        metadata = build_metadata("8.4.0", None)
        table = build_events_table([["onset", "HED"], [1.0, "Red"]])
        nwbfile = build_nwbfile(metadata, table)
        self.assertIs(nwbfile.lab_meta_data["hed_schema"], metadata)
        self.assertIn("events", nwbfile.acquisition)
        self.assertEqual(len(build_nwbfile(metadata, None).acquisition), 0)


if __name__ == "__main__":
    unittest.main()
