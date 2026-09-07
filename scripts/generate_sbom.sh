#!/usr/bin/env bash
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
output="$repo_root/sbom/cyclonedx-python.json"
mkdir -p "$(dirname -- "$output")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to generate the SBOM." >&2
  exit 1
fi

cd "$repo_root"
uv run --locked --with cyclonedx-bom cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --output-format JSON --output-file "$output" .venv
if [[ ! -s "$output" ]]; then
  echo "SBOM output is missing or empty: $output" >&2
  exit 1
fi
echo "SBOM_GENERATED $output"
