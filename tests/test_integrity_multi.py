import json
from pathlib import Path
import tempfile
import unittest

from integrity_multi import ScopeError, compare, flatten, run, snapshot


class MultiIntegrityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "configs").mkdir()
        (self.root / "configs/dsp.json").write_text(json.dumps({"audio": {"gain": -3, "mute": False}}))
        self.scope = {"files": [], "directories": ["configs"]}
        self.baseline = self.root / "reports/baseline.json"

    def test_no_drift_after_formatting_only_change(self):
        run("baseline", self.root, self.scope, self.baseline)
        (self.root / "configs/dsp.json").write_text(' {"audio": {"mute": false, "gain": -3}} ')
        self.assertEqual(run("check", self.root, self.scope, self.baseline)["status"], "PASS")

    def test_nested_change_and_file_added(self):
        run("baseline", self.root, self.scope, self.baseline)
        (self.root / "configs/dsp.json").write_text('{"audio":{"gain":-6,"mute":false}}')
        (self.root / "configs/new.json").write_text('{"enabled":true}')
        result = run("check", self.root, self.scope, self.baseline)
        self.assertEqual(result["status"], "CHANGED")
        self.assertIn({"file": "configs/dsp.json", "path": "/audio/gain", "change": "MODIFIED"}, result["changes"])
        self.assertIn({"file": "configs/new.json", "path": "/", "change": "ADDED_FILE"}, result["changes"])
        self.assertNotIn("-6", json.dumps(result))

    def test_removed_file(self):
        run("baseline", self.root, self.scope, self.baseline)
        (self.root / "configs/dsp.json").unlink()
        result = run("check", self.root, self.scope, self.baseline)
        self.assertEqual(result["changes"][0]["change"], "REMOVED_FILE")

    def test_added_nested_key(self):
        before = {"x": flatten({"a": {"b": 2}})}
        after = {"x": flatten({"a": {"b": 2, "c": 3}})}
        self.assertEqual(compare(before, after)[0]["path"], "/a/c")
        self.assertEqual(compare(before, after)[0]["change"], "ADDED")

    def test_refuse_overwriting_baseline(self):
        run("baseline", self.root, self.scope, self.baseline)
        with self.assertRaises(ScopeError):
            run("baseline", self.root, self.scope, self.baseline)

    def test_block_symlink(self):
        (self.root / "configs/link.json").symlink_to(self.root / "configs/dsp.json")
        with self.assertRaises(ScopeError):
            snapshot(self.root, self.scope)


if __name__ == "__main__":
    unittest.main()
