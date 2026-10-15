
```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_GATE = REPO_ROOT / "policy_gate.py"

POLICY = """
fail_on:
  critical_count_exceeds: 0
  high_count_exceeds: 10
warn_on:
  medium_count_exceeds: 50
report_label: "Lab 34 Docker Image Security"
"""


class TestPolicyGate(unittest.TestCase):
    def run_policy(self, severities):
        report = {
            "Results": [
                {
                    "Target": "test-image",
                    "Vulnerabilities": [
                        {"Severity": severity}
                        for severity in severities
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "report.json"
            policy_path = temp_path / "policy.yaml"

            report_path.write_text(json.dumps(report), encoding="utf-8")
            policy_path.write_text(POLICY, encoding="utf-8")

            return subprocess.run(
                [
                    sys.executable,
                    str(POLICY_GATE),
                    str(report_path),
                    str(policy_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_clean_report_passes(self):
        result = self.run_policy([])
        self.assertEqual(result.returncode, 0)

    def test_critical_vulnerability_fails(self):
        result = self.run_policy(["CRITICAL"])
        self.assertEqual(result.returncode, 1)

    def test_more_than_ten_high_vulnerabilities_fails(self):
        result = self.run_policy(["HIGH"] * 11)
        self.assertEqual(result.returncode, 1)

    def test_ten_high_vulnerabilities_pass(self):
        result = self.run_policy(["HIGH"] * 10)
        self.assertEqual(result.returncode, 0)

    def test_medium_warning_does_not_fail_policy(self):
        result = self.run_policy(["MEDIUM"] * 51)
        self.assertEqual(result.returncode, 0)

    def test_invalid_report_returns_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "report.json"
            policy_path = temp_path / "policy.yaml"

            report_path.write_text("{invalid json", encoding="utf-8")
            policy_path.write_text(POLICY, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(POLICY_GATE),
                    str(report_path),
                    str(policy_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
```
