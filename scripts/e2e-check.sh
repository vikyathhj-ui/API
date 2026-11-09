#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# End-to-end check of a RUNNING stack, from a customer's point of view:
#   1. sign up for a free key over HTTP
#   2. generate the sample invoices through the API
#   3. check the PDFs with tools we did not write (veraPDF, Mustang), offline
#   4. send the PDFs back to /v1/validate
#   5. read /v1/usage
# Usage:  bash scripts/e2e-check.sh   [BASE_URL=http://127.0.0.1:8000] [API_KEY=ifk_live_...]
#         (without API_KEY it signs up for a new free key; sign-up is limited to 3/hour per IP)
# Needs: Docker, curl, python3 (only for reading JSON).
# -----------------------------------------------------------------------------
set -uo pipefail
cd "$(dirname "$0")/.."
BASE="${BASE_URL:-http://127.0.0.1:8000}"
WORK="$(mktemp -d)"; chmod 755 "$WORK"; trap 'rm -rf "$WORK"' EXIT
TOOLS="scripts/.tools"; mkdir -p "$TOOLS"
VERAPDF_IMAGE="verapdf/cli@sha256:d74b7026c18a0f171e73c153b617fe6520e1511feb24ca98a348b2bb897669fb"  # 1.30.3
JRE_IMAGE="eclipse-temurin:21-jre-jammy@sha256:1eac8b8fee11ca7d6725a48bc5d41992ed1561504ebae25490d2d062847e8269"
MUSTANG_SHA256="42d7868cb68264874a7b8cab4c3587b03b23ccc7cd72373da917f66758bb9736"                  # 2.26.0
pass=0; fail=0
ok()  { echo "  PASS  $*"; pass=$((pass+1)); }
bad() { echo "  FAIL  $*"; fail=$((fail+1)); }
json() { python3 -c "import sys,json; d=json.load(sys.stdin); print($1)"; }

if [[ ! -f "$TOOLS/Mustang-CLI.jar" ]]; then
  curl -fsSL -o "$TOOLS/Mustang-CLI.jar" \
    https://repo.maven.apache.org/maven2/org/mustangproject/Mustang-CLI/2.26.0/Mustang-CLI-2.26.0.jar
fi
sum="$( (sha256sum "$TOOLS/Mustang-CLI.jar" 2>/dev/null || shasum -a 256 "$TOOLS/Mustang-CLI.jar") | cut -d' ' -f1)"
[[ "$sum" == "$MUSTANG_SHA256" ]] || { echo "Mustang checksum mismatch"; rm -f "$TOOLS/Mustang-CLI.jar"; exit 1; }

echo "== Service at $BASE"
[[ "$(curl -s "$BASE/v1/health" | json 'd["status"]')" == "ok" ]] && ok "health" || { bad "health"; exit 1; }

if [[ -n "${API_KEY:-}" ]]; then
  KEY="$API_KEY"; echo "== Using API_KEY from environment"
else
  echo "== Sign up"
  KEY="$(curl -s -X POST "$BASE/v1/signup" -H 'Content-Type: application/json' \
         -d "{\"email\":\"e2e-$(date +%s)-$RANDOM@example.com\"}" | json 'd.get("api_key","")')"
  [[ "$KEY" == ifk_live_* ]] && ok "free API key issued" \
    || { bad "signup refused (3/hour per IP limit?) - rerun with API_KEY=<key from the admin CLI>"; exit 1; }
fi
before="$(curl -s "$BASE/v1/usage" -H "Authorization: Bearer $KEY" | json 'd["documents_used"]')"

for sample in fr-consulting de-mixed-vat; do
  echo "== $sample"
  code="$(curl -s -o "$WORK/$sample.pdf" -w '%{http_code}' -X POST "$BASE/v1/invoices" \
          -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
          --data-binary "@service/samples/$sample.json")"
  chmod 644 "$WORK/$sample.pdf" 2>/dev/null
  [[ "$code" == 200 ]] && ok "generated PDF ($(wc -c < "$WORK/$sample.pdf") bytes)" || bad "generate HTTP $code"

  vp="$(docker run --rm --network none -v "$WORK:/data:ro" "$VERAPDF_IMAGE" --flavour 3b --format text "/data/$sample.pdf" 2>&1 | tail -1)"
  [[ "$vp" == PASS* ]] && ok "veraPDF PDF/A-3b" || bad "veraPDF: $vp"

  docker run --rm --network none -v "$PWD/$TOOLS:/m:ro" -v "$WORK:/data:ro" "$JRE_IMAGE" \
    java -jar /m/Mustang-CLI.jar --no-notices --action validate --source "/data/$sample.pdf" > "$WORK/m.xml" 2>/dev/null
  status="$(grep -oE '<summary status="[a-z]+"/>' "$WORK/m.xml" | tail -1 | grep -oE 'valid|invalid')"
  warns="$(grep -oE '\[ID [A-Za-z0-9_.-]+\]' "$WORK/m.xml" | sort -u | tr '\n' ' ')"
  [[ "$status" == valid && -z "$warns" ]] && ok "Mustang Factur-X: valid, no warnings" || bad "Mustang: $status $warns"

  v="$(curl -s -X POST "$BASE/v1/validate" -H "Authorization: Bearer $KEY" -H 'Content-Type: application/pdf' \
       --data-binary "@$WORK/$sample.pdf" | json '(d["valid"], len(d["errors"]), len(d["warnings"]))')"
  [[ "$v" == "(True, 0, 0)" ]] && ok "/v1/validate: valid, 0 errors, 0 warnings" || bad "/v1/validate: $v"
done

echo "== Usage"
used="$(curl -s "$BASE/v1/usage" -H "Authorization: Bearer $KEY" | json 'd["documents_used"]')"
[[ "$((used - before))" == 4 ]] && ok "usage counted: +4 documents" || bad "usage went $before -> $used (expected +4)"

echo "----"
echo "Passed: $pass   Failed: $fail"
[[ $fail -eq 0 ]]
