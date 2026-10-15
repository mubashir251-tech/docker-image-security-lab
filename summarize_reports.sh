
#!/usr/bin/env bash
set -euo pipefail

REPORTS_DIR="${1:-reports}"
OUTPUT_FILE="${REPORTS_DIR}/summary.md"

if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required." >&2
    exit 1
fi

shopt -s nullglob
files=("$REPORTS_DIR"/*-trivy.json)

if (( ${#files[@]} == 0 )); then
    echo "Error: No Trivy JSON reports found in $REPORTS_DIR" >&2
    exit 1
fi

{
    echo "# Docker Image Vulnerability Summary"
    echo
    echo "Generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
    echo
    echo "| Image | Critical | High | Medium | Low |"
    echo "|---|---:|---:|---:|---:|"

    for file in "${files[@]}"; do
        if ! jq -e 'type == "object" and (.Results | type == "array")' \
            "$file" >/dev/null; then
            echo "Error: Invalid Trivy report: $file" >&2
            exit 1
        fi

        image="${file##*/}"
        image="${image%-trivy.json}"

        counts=$(jq -r '
            [.Results[]?.Vulnerabilities[]?.Severity // empty] as $s
            | [
                ([$s[] | select(. == "CRITICAL")] | length),
                ([$s[] | select(. == "HIGH")] | length),
                ([$s[] | select(. == "MEDIUM")] | length),
                ([$s[] | select(. == "LOW")] | length)
              ]
            | @tsv
        ' "$file")

        printf '| %s | %s |\n' "$image" "${counts//$'\t'/ | }"
    done
} > "$OUTPUT_FILE"

echo "Summary saved to: $OUTPUT_FILE"
