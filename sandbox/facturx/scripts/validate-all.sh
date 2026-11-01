#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# validate-all.sh: checks every generated Factur-X PDF in ./out with tools
# we did NOT write ourselves (so we are not "grading our own homework"):
#
#   1. Round-trip    : the XML inside the PDF is byte-identical to the XML we generated
#   2. KoSIT         : EN 16931 business rules on the XML (validator container from ../validator)
#   3. veraPDF       : the PDF is a valid PDF/A-3b archive file
#   4. Mustang       : full Factur-X/ZUGFeRD check (PDF + XML + metadata + French rules)
#
# Needs: Docker running, ../validator container up (docker compose up -d there),
#        generated files in ./out (docker compose run --rm generator ...)
# Usage: bash scripts/validate-all.sh
# -----------------------------------------------------------------------------
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$HERE/out"
KOSIT_URL="${KOSIT_URL:-http://127.0.0.1:8080}"
TOOLS="$HERE/vendor"

# Pinned tool versions
VERAPDF_IMAGE="verapdf/cli@sha256:d74b7026c18a0f171e73c153b617fe6520e1511feb24ca98a348b2bb897669fb"  # veraPDF 1.30.3
JRE_IMAGE="eclipse-temurin:21-jre-jammy@sha256:1eac8b8fee11ca7d6725a48bc5d41992ed1561504ebae25490d2d062847e8269"
MUSTANG_VERSION="2.26.0"
MUSTANG_SHA256="42d7868cb68264874a7b8cab4c3587b03b23ccc7cd72373da917f66758bb9736"

pass=0; fail=0
ok()  { echo "  PASS  $*"; pass=$((pass+1)); }
bad() { echo "  FAIL  $*"; fail=$((fail+1)); }

# Download Mustang once (pinned + checksum verified)
mkdir -p "$TOOLS"
if [[ ! -f "$TOOLS/Mustang-CLI.jar" ]]; then
  echo "Downloading Mustang CLI $MUSTANG_VERSION ..."
  curl -fsSL -o "$TOOLS/Mustang-CLI.jar" \
    "https://repo.maven.apache.org/maven2/org/mustangproject/Mustang-CLI/$MUSTANG_VERSION/Mustang-CLI-$MUSTANG_VERSION.jar"
fi
actual="$( (sha256sum "$TOOLS/Mustang-CLI.jar" 2>/dev/null || shasum -a 256 "$TOOLS/Mustang-CLI.jar") | cut -d' ' -f1)"
[[ "$actual" == "$MUSTANG_SHA256" ]] || { echo "Mustang checksum mismatch: $actual"; rm -f "$TOOLS/Mustang-CLI.jar"; exit 1; }

shopt -s nullglob
pdfs=("$OUT"/*.pdf)
[[ ${#pdfs[@]} -gt 0 ]] || { echo "No PDFs in $OUT. Generate some first."; exit 1; }

for pdf in "${pdfs[@]}"; do
  name="$(basename "$pdf" .pdf)"
  echo "== $name"

  # 1. Round trip: extract embedded XML with the generator image's Python
  # (set FX_PYTHON=/path/to/python to run this step without the generator image)
  if [[ -n "${FX_PYTHON:-}" ]]; then
    rt=(bash -c 'cd "$0" && "$1" -m app.roundtrip "out/$2.pdf" "out/$2.xml"' "$HERE" "$FX_PYTHON" "$name")
  else
    rt=(docker compose -f "$HERE/docker-compose.yml" run --rm -T --entrypoint python generator
        -m app.roundtrip "/work/out/$name.pdf" "/work/out/$name.xml")
  fi
  if "${rt[@]}" > /dev/null; then
    ok "round-trip: embedded factur-x.xml identical to generated XML"
  else
    bad "round-trip: embedded XML differs or missing"
  fi

  # 2. KoSIT EN 16931 rules
  code="$(curl -s -o "/tmp/kosit-$name.xml" -w '%{http_code}' -X POST -H 'Content-Type: application/xml' \
          --data-binary "@$OUT/$name.xml" "$KOSIT_URL/$name.xml")"
  msgs="$(grep -c '<rep:message' "/tmp/kosit-$name.xml" 2>/dev/null || true)"
  [[ "$code" == "200" ]] && ok "KoSIT EN 16931: acceptable ($msgs messages)" \
                         || bad "KoSIT EN 16931: HTTP $code ($msgs messages, see /tmp/kosit-$name.xml)"

  # 3. veraPDF PDF/A-3b (offline container)
  vp="$(docker run --rm --network none -v "$OUT:/data:ro" "$VERAPDF_IMAGE" --flavour 3b --format text "/data/$name.pdf" 2>&1 | tail -1)"
  [[ "$vp" == PASS* ]] && ok "veraPDF: $vp" || bad "veraPDF: $vp"

  # 4. Mustang Factur-X validation (offline container)
  docker run --rm --network none -v "$TOOLS:/m:ro" -v "$OUT:/data:ro" "$JRE_IMAGE" \
    java -jar /m/Mustang-CLI.jar --no-notices --action validate --source "/data/$name.pdf" \
    > "/tmp/mustang-$name.xml" 2> /dev/null
  status="$(grep -oE '<summary status="[a-z]+"/>' "/tmp/mustang-$name.xml" | tail -1 | grep -oE 'valid|invalid')"
  warnings="$(grep -oE '\[ID [A-Za-z0-9_.-]+\]' "/tmp/mustang-$name.xml" | sort -u | tr '\n' ' ')"
  if [[ "$status" == "valid" && -z "$warnings" ]]; then ok "Mustang: valid, no warnings"
  elif [[ "$status" == "valid" ]]; then ok "Mustang: valid, warnings: $warnings"
  else bad "Mustang: ${status:-no result} $warnings (see /tmp/mustang-$name.xml)"; fi
done

echo "----"
echo "Passed: $pass   Failed: $fail"
[[ $fail -eq 0 ]]
