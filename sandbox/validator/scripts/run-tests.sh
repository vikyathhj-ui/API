#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# run-tests.sh: checks the running validator container over HTTP.
#
# For every sample invoice we know what the answer SHOULD be:
#   samples/valid/*    -> HTTP 200 (acceptable)
#   samples/invalid/*  -> HTTP 406 (not acceptable)
# and for some broken samples, which business rule should complain.
#
# Usage:  bash scripts/run-tests.sh            (container must be running)
#         VALIDATOR_URL=http://host:port bash scripts/run-tests.sh
# -----------------------------------------------------------------------------
set -uo pipefail

URL="${VALIDATOR_URL:-http://127.0.0.1:8080}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pass=0; fail=0

check() { # file expected_http_status [expected_text_in_report]
  local file="$1" want="$2" text="${3:-}" body code
  body="$(mktemp)"
  code="$(curl -sS -o "$body" -w '%{http_code}' -X POST \
          -H 'Content-Type: application/xml' --data-binary "@$file" \
          "$URL/$(basename "$file")")"
  if [[ "$code" == "$want" ]] && { [[ -z "$text" ]] || grep -q -- "$text" "$body"; }; then
    echo "PASS  $(basename "$file")  -> HTTP $code ${text:+(found $text)}"
    pass=$((pass+1))
  else
    echo "FAIL  $(basename "$file")  -> HTTP $code, expected $want ${text:+and '$text' in report}"
    fail=$((fail+1))
  fi
  rm -f "$body"
}

echo "Testing validator at $URL"
curl -fsS "$URL/server/health" > /dev/null && echo "PASS  health endpoint" && pass=$((pass+1)) \
  || { echo "FAIL  health endpoint (is the container running?)"; exit 1; }

for f in "$HERE"/samples/valid/*.xml; do check "$f" 200; done

check "$HERE/samples/invalid/wrong-payable-amount-ubl.xml" 406 "BR-CO-16"
check "$HERE/samples/invalid/missing-issue-date-ubl.xml"   406 "cvc-complex-type"
check "$HERE/samples/invalid/not-an-invoice.xml"           406

echo "----"
echo "Passed: $pass   Failed: $fail"
[[ $fail -eq 0 ]]
