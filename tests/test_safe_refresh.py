"""Offline safety tests: python3 -m unittest discover -s tests -p 'test_safe_refresh.py' -v"""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_data.py"
spec = importlib.util.spec_from_file_location("hyoja_fetch", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(identifier="X1", gu="수지구", title="검증기관"):
    return {"hpid": identifier, "dutyName": title,
            "dutyAddr": "경기도 용인시 " + gu + " 풍덕천로 1"}


class SafeRefreshTests(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(mod.validate("pharmacy", [row()]), 1)

    def test_empty(self):
        with self.assertRaises(ValueError):
            mod.validate("pharmacy", [])

    def test_missing_fields(self):
        for key in ("hpid", "dutyName", "dutyAddr"):
            with self.subTest(key=key):
                item = row()
                item[key] = ""
                with self.assertRaises(ValueError):
                    mod.validate("pharmacy", [item])

    def test_duplicate_identifier(self):
        with self.assertRaises(ValueError):
            mod.validate("pharmacy", [row(), row()])

    def test_wrong_region(self):
        with self.assertRaises(ValueError):
            mod.validate("pharmacy", [row(gu="성남시")])

    def test_api_second_dataset_failure_preserves_files(self):
        with tempfile.TemporaryDirectory() as directory:
            original = {"기존": True}
            for name in ("emergency", "pharmacy", "status"):
                (Path(directory) / (name + ".json")).write_text(
                    json.dumps(original), encoding="utf-8")
            def fake_fetch(path, label):
                if "Parmacy" in path:
                    raise RuntimeError("simulated API failure")
                return [row()]
            with patch.object(mod, "KEY", "test-only"), patch.object(mod, "OUT", directory), patch.object(mod, "fetch", side_effect=fake_fetch):
                with self.assertRaises(RuntimeError):
                    mod.main()
            for name in ("emergency", "pharmacy", "status"):
                self.assertEqual(json.loads((Path(directory) / (name + ".json")).read_text(encoding="utf-8")), original)

    def test_missing_key_preserves_files(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(mod, "KEY", ""), patch.object(mod, "OUT", directory):
                with self.assertRaises(RuntimeError):
                    mod.main()
            self.assertEqual(os.listdir(directory), [])

    def test_success_writes_consistent_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(mod, "KEY", "test-only"), patch.object(mod, "OUT", directory), patch.object(mod, "fetch", side_effect=[[row("E")], [row("P")]]):
                mod.main()
            for name in ("emergency", "pharmacy"):
                self.assertEqual(json.loads((Path(directory) / (name + ".json")).read_text(encoding="utf-8"))["건수"], 1)
            status = json.loads((Path(directory) / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["emergency"]["상태"], "성공")
            self.assertEqual(status["pharmacy"]["상태"], "성공")


if __name__ == "__main__":
    unittest.main()
