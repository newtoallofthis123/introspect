from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path

from introspect import storage, timestamps


class TimestampTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_root = storage.ROOT
        storage.ROOT = Path(self.tmp.name)
        storage.ensure("run-1")

    def tearDown(self) -> None:
        storage.ROOT = self.old_root
        self.tmp.cleanup()

    def test_parse_duration(self) -> None:
        self.assertEqual(timestamps.parse_duration("5m"), datetime.timedelta(minutes=5))
        self.assertEqual(timestamps.parse_duration("250ms"), datetime.timedelta(milliseconds=250))
        self.assertIsNone(timestamps.parse_duration("5w"))

    def test_line_at_or_after_uses_fixed_width_records(self) -> None:
        base = datetime.datetime(2026, 1, 1, 12, 0, 0)
        records = [
            base.strftime(timestamps.TS_FMT).encode() + b"\n",
            (base + datetime.timedelta(seconds=10)).strftime(timestamps.TS_FMT).encode() + b"\n",
            (base + datetime.timedelta(seconds=20)).strftime(timestamps.TS_FMT).encode() + b"\n",
        ]
        timestamps.ts_path("run-1").write_bytes(b"".join(records))

        target = base + datetime.timedelta(seconds=11)
        self.assertEqual(timestamps.line_at_or_after("run-1", target), 3)
        self.assertEqual(timestamps.ts_at_line("run-1", 2), base + datetime.timedelta(seconds=10))


if __name__ == "__main__":
    unittest.main()
