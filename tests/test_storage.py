from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from introspect import storage


class StorageTests(unittest.TestCase):
    def test_validate_id_accepts_safe_names(self) -> None:
        for id_ in ["app", "app-1", "app_1", "app.1", "A0._-"]:
            self.assertEqual(storage.validate_id(id_), id_)

    def test_validate_id_rejects_path_like_names(self) -> None:
        for id_ in ["", ".", "..", "a/b", "../x", "x y", "x:y"]:
            with self.subTest(id_=id_):
                with self.assertRaises(ValueError):
                    storage.validate_id(id_)

    def test_ensure_uses_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_root = storage.ROOT
            storage.ROOT = Path(tmp)
            try:
                path = storage.ensure("run-1")
                self.assertEqual(path, Path(tmp) / "run-1")
                self.assertTrue(path.is_dir())
            finally:
                storage.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
