#!/usr/bin/env bash
# Usage: scripts/smoke_test.sh BASE_URL [EXPECTED_MODEL_VERSION]
#
# Waits for /health, checks the served model version if given, sends one /predict,
# then checks that both pages of the site are served.
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

for page in / /stats/; do
  curl -sf "$url$page" | grep -q '<div id="root">' || { echo "page $page is not served"; exit 1; }
  echo "page $page ok"
done
