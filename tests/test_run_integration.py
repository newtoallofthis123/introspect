from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from introspect import reader, run, storage


@unittest.skipIf(os.name == "nt", "introspect run uses Unix pty APIs")
class RunIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_root = storage.ROOT
        storage.ROOT = Path(self.tmp.name)

    def tearDown(self) -> None:
        storage.ROOT = self.old_root
        self.tmp.cleanup()

    def test_run_captures_output_and_exit_status(self) -> None:
        old_stdout = os.dup(1)
        with open(os.devnull, "wb") as devnull:
            os.dup2(devnull.fileno(), 1)
            try:
                status = run.run([sys.executable, "-c", "print('hello'); raise SystemExit(7)"], id_="smoke")
            finally:
                os.dup2(old_stdout, 1)
                os.close(old_stdout)

        self.assertEqual(status, 7)
        self.assertEqual(reader.read_lines("smoke"), [b"hello"])
        meta = storage.read_meta("smoke")
        self.assertEqual(meta["cmd"][0], sys.executable)
        self.assertIsNotNone(meta["exited"])


if __name__ == "__main__":
    unittest.main()
