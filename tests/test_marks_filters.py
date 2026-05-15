from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from introspect import filters, marks, storage, timestamps


class MarksFiltersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_root = storage.ROOT
        storage.ROOT = Path(self.tmp.name)
        storage.ensure("run-1")

    def tearDown(self) -> None:
        storage.ROOT = self.old_root
        self.tmp.cleanup()

    def test_filters_round_trip_through_meta(self) -> None:
        filters.set_("run-1", "error", r"\bERROR\b")
        self.assertEqual(filters.get("run-1", "error"), r"\bERROR\b")
        self.assertEqual(filters.list_("run-1"), {"error": r"\bERROR\b"})
        self.assertTrue(filters.remove("run-1", "error"))
        self.assertEqual(filters.list_("run-1"), {})

    def test_marks_replace_existing_name(self) -> None:
        d = storage.id_dir("run-1")
        (d / "log").write_bytes(b"one\ntwo\n")
        (d / "ts.log").write_bytes(timestamps.now_ts_bytes() * 2)

        first = marks.add("run-1", "deploy", note="before")
        second = marks.add("run-1", "deploy", note="after")

        self.assertEqual(first["line"], 2)
        self.assertEqual(second["line"], 2)
        self.assertEqual(marks.list_("run-1"), [second])
        self.assertEqual(marks.find("run-1", "deploy"), second)
        self.assertTrue(marks.remove("run-1", "deploy"))
        self.assertEqual(marks.list_("run-1"), [])


if __name__ == "__main__":
    unittest.main()
