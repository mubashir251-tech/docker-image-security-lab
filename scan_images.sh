#!/usr/bin/env bash

set -u

scan_with_trivy() {
    local image="$1"
    local output_file="$2"
    local temp_file="${output_file}.tmp"

    echo "[Trivy] Scanning ${image}..."

    if trivy image --format json --output "$temp_file" "$image"; then
        mv "$temp_file" "$output_file"
        echo "[Trivy] Report saved: $output_file"
    else
        local rc=$?
        rm -f "$temp_file"
        echo "[Trivy] Scan failed for $image" >&2
        return "$rc"
    fi
}


scan_with_grype() {
    local image="$1"
    local output_file="$2"
    local temp_file="${output_file}.tmp"

    echo "[Grype] Scanning ${image}..."

    if ! grype "$image" --output json > "$temp_file"; then
        echo "[Grype] Scan failed for $image" >&2
        rm -f "$temp_file"
        return 1
    fi

    if [[ ! -s "$temp_file" ]] ||
       ! jq -e '.matches | type == "array"' "$temp_file" >/dev/null; then
        echo "[Grype] Empty or invalid JSON report for $image" >&2
        rm -f "$temp_file"
        return 1
    fi

    if ! mv "$temp_file" "$output_file"; then
        echo "[Grype] Could not save report: $output_file" >&2
        rm -f "$temp_file"
        return 1
    fi

    echo "[Grype] Valid report saved: $output_file"
}

run_contrast_scan() {
    local image_list="$1"
    local reports_dir="$2"
    local image filename
    local failures=0

    if [[ ! -f "$image_list" ]]; then
        echo "Image list not found: $image_list" >&2
        return 1
    fi

    mkdir -p "$reports_dir"

    while IFS= read -r image || [[ -n "$image" ]]; do
        [[ -z "$image" || "$image" == \#* ]] && continue

        filename="${image//:/-}"
        filename="${filename//\//-}"

        scan_with_trivy "$image" "$reports_dir/${filename}-trivy.json" || failures=$((failures + 1))
        scan_with_grype "$image" "$reports_dir/${filename}-grype.json" || failures=$((failures + 1))
    done < "$image_list"

    if (( failures > 0 )); then
        echo "Completed with $failures scanner failure(s)." >&2
        return 1
    fi

    echo "All image scans completed successfully."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    run_contrast_scan "${1:-images.txt}" "${2:-reports}"
fi
