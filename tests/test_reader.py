from __future__ import annotations

import re
import unittest

from introspect import reader


class ReaderTests(unittest.TestCase):
    def test_split_lines_strips_ansi_and_normalizes_crlf(self) -> None:
        data = b"\x1b[31merror\x1b[0m\r\nok\n"
        self.assertEqual(reader.split_lines(data), [b"error", b"ok"])

    def test_split_lines_keeps_final_partial_line(self) -> None:
        self.assertEqual(reader.split_lines(b"one\ntwo"), [b"one", b"two"])

    def test_apply_filter_matches_bytes_regex(self) -> None:
        lines = [(1, b"ok"), (2, b"ERROR failed")]
        self.assertEqual(reader.apply_filter(lines, re.compile(rb"ERROR")), [(2, b"ERROR failed")])


if __name__ == "__main__":
    unittest.main()
