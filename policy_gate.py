
#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import yaml


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} TRIVY_REPORT.json policy.yaml",
            file=sys.stderr,
        )
        return 2

    report_path = Path(sys.argv[1])
    policy_path = Path(sys.argv[2])

    try:
        with report_path.open(encoding="utf-8") as file:
            report = json.load(file)

        with policy_path.open(encoding="utf-8") as file:
            policy = yaml.safe_load(file)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"Error reading report or policy: {error}", file=sys.stderr)
        return 2

    if not isinstance(report, dict) or not isinstance(report.get("Results"), list):
        print("Error: Invalid Trivy report structure.", file=sys.stderr)
        return 2

    if not isinstance(policy, dict):
        print("Error: Policy must be a YAML mapping.", file=sys.stderr)
        return 2

    fail_on = policy.get("fail_on", {})
    warn_on = policy.get("warn_on", {})

    if not isinstance(fail_on, dict) or not isinstance(warn_on, dict):
        print("Error: fail_on and warn_on must be YAML mappings.", file=sys.stderr)
        return 2

    thresholds = {
        "CRITICAL": fail_on.get("critical_count_exceeds", 0),
        "HIGH": fail_on.get("high_count_exceeds", 10),
        "MEDIUM": warn_on.get("medium_count_exceeds", 50),
    }

    for severity, threshold in thresholds.items():
        if type(threshold) is not int or threshold < 0:
            print(f"Error: Invalid threshold for {severity}.", file=sys.stderr)
            return 2

    counts = {severity: 0 for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}

    for result in report["Results"]:
        if not isinstance(result, dict):
            continue

        vulnerabilities = result.get("Vulnerabilities") or []
        if not isinstance(vulnerabilities, list):
            continue

        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                continue

            severity = vulnerability.get("Severity")
            if severity in counts:
                counts[severity] += 1

    label = policy.get("report_label", "Docker Image Security Policy")
    print(f"Policy: {label}")
    print(f"Report: {report_path}")

    for severity, count in counts.items():
        print(f"{severity}: {count}")

    failed = False

    for severity in ("CRITICAL", "HIGH"):
        threshold = thresholds[severity]
        if counts[severity] > threshold:
            print(
                f"FAIL: {severity} count {counts[severity]} "
                f"exceeds threshold {threshold}."
            )
            failed = True

    medium_threshold = thresholds["MEDIUM"]
    if counts["MEDIUM"] > medium_threshold:
        print(
            f"WARNING: MEDIUM count {counts['MEDIUM']} "
            f"exceeds warning threshold {medium_threshold}."
        )

    if failed:
        print("POLICY RESULT: FAIL")
        return 1

    print("POLICY RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
