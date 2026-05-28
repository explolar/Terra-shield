#!/usr/bin/env bash
# Submit a Cloud Build asynchronously, then poll its status slowly.
#
# `gcloud builds submit` polls the build once per second. A multi-minute build
# therefore issues ~60 status GETs/min and trips the 60 GET/min/user quota on
# cloudbuild.googleapis.com (RESOURCE_EXHAUSTED 429) — killing the CLI while the
# build itself keeps running. Submitting with --async and polling every 15s
# keeps us at ~4 GETs/min, well under the limit, and still waits for the result.
#
# Usage: infra/cloudbuild-wait.sh <config-path> <substitutions> [source-dir]
set -euo pipefail

CONFIG="$1"
SUBS="$2"
SRC="${3:-.}"

BUILD_ID=$(gcloud builds submit "$SRC" \
  --config "$CONFIG" \
  --substitutions="$SUBS" \
  --async \
  --format='value(id)')
echo "Submitted Cloud Build $BUILD_ID (config=$CONFIG)"

while true; do
  STATUS=$(gcloud builds describe "$BUILD_ID" --format='value(status)')
  echo "  build $BUILD_ID: $STATUS"
  case "$STATUS" in
    SUCCESS) break ;;
    FAILURE|TIMEOUT|CANCELLED|EXPIRED|INTERNAL_ERROR)
      echo "Cloud Build $BUILD_ID ended with status $STATUS" >&2
      echo "Logs: https://console.cloud.google.com/cloud-build/builds/$BUILD_ID" >&2
      exit 1 ;;
  esac
  sleep 15
done
echo "Cloud Build $BUILD_ID succeeded."
