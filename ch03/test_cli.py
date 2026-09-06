import json
from pathlib import Path
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, "evaluate.py", *args],
            cwd=Path(__file__).resolve().parent,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, timeout=10,
        )

    def test_default_report_retains_successes_and_failures(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        reports = json.loads(result.stdout)["reports"]
        self.assertEqual([r["summary"]["passed"] for r in reports], [2, 5])
        self.assertEqual([len(r["trials"]) for r in reports], [5, 5])

    def test_pass_gate_sets_exit_code_without_discarding_report(self):
        for candidate, code in (("baseline", 1), ("scripted", 0)):
            with self.subTest(candidate=candidate):
                result = self.invoke("--candidate", candidate, "--require-pass")
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(len(json.loads(result.stdout)["reports"][0]["trials"]), 5)

    def test_invalid_configuration_stops_before_any_trials(self):
        for args in (("--repeats", "0"), ("--candidate", "live")):
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
