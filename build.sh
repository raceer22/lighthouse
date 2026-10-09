#!/usr/bin/env bash
# Validate the manifest, then build the extension zip.
# Usage: ./build.sh [output-dir]   (default: dist)
set -euo pipefail

SOURCE="$(dirname "$0")/lighthouse"
BLENDER="${BLENDER:-blender}"
OUT="${1:-dist}"

"$BLENDER" --factory-startup --command extension validate "$SOURCE"
mkdir -p "$OUT"
"$BLENDER" --factory-startup --command extension build --source-dir "$SOURCE" --output-dir "$OUT"
