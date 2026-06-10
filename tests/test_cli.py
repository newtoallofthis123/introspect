from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from unittest import mock

from introspect import cli


class CliTests(unittest.TestCase):
    def test_main_reports_invalid_id_without_traceback(self) -> None:
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["introspect", "get-lines", "bad/id"]):
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as cm:
                    cli.main()

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("invalid id", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_shell_refuses_to_nest(self) -> None:
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"INTROSPECT_ID": "outer"}):
            with mock.patch.object(sys, "argv", ["introspect", "shell"]):
                with contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as cm:
                        cli.main()

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("outer", err.getvalue())


if __name__ == "__main__":
    unittest.main()
