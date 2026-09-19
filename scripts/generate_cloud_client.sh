#!/usr/bin/env bash
# Regenerate only the private client; never the public Computer interface.
set -euo pipefail
cd "$(dirname "$0")/.."
uvx openapi-python-client==0.29.1 generate \
  --path openapi/cloud.json \
  --config openapi/python-client.yaml \
  --meta none \
  --output-path src/_celesto_cloud_api \
  --overwrite
uvx ruff==0.15.6 format --isolated src/_celesto_cloud_api
