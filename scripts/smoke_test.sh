#!/usr/bin/env bash
# Usage: scripts/smoke_test.sh BASE_URL [EXPECTED_MODEL_VERSION]
#
# Waits for /health, checks the served model version if given, then sends one /predict.
set -euo pipefail

url="$1"
expected="${2:-}"

for _ in $(seq 1 30); do
  curl -sf "$url/health" > /dev/null && break
  sleep 1
done

health=$(curl -sf "$url/health")
echo "$health"
if [ -n "$expected" ]; then
  actual=$(echo "$health" | jq -r .model_version)
  [ "$actual" = "$expected" ] || { echo "expected model $expected, got $actual"; exit 1; }
fi

curl -sf -X POST "$url/predict" \
  -H 'Content-Type: application/json' \
  -d '{"url": "http://1.2.3.4/x.exe"}'
echo
