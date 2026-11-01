#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# fetch-dependencies.sh
#
# Downloads the third-party parts this sandbox needs, at EXACT pinned versions,
# and checks each one against a pinned checksum or git commit. If anything has
# been tampered with or changed upstream, the script stops with an error.
#
# What it downloads (all public, all open-source):
#   1. KoSIT Validator engine (Java .jar)        - Apache 2.0  - Maven Central
#   2. UBL 2.1 XML Schemas (unmodified OASIS files, as shipped in KoSIT's
#      Peppol BIS configuration)                 - OASIS / Apache 2.0 - GitHub (git)
#   3. EN 16931 validation rules + CII schemas    - EUPL 1.2    - GitHub (git)
#   4. Report stylesheets from KoSIT's XRechnung configuration - Apache 2.0 - GitHub (git)
#
# Output: ./vendor/  (ignored by git; recreate any time with this script)
#
# Usage:  bash scripts/fetch-dependencies.sh
# Needs:  bash, curl, git, sha256sum (or shasum on macOS)
# -----------------------------------------------------------------------------
set -euo pipefail

# ---- Pinned versions (change these deliberately, never "latest") -------------
VALIDATOR_VERSION="1.6.3"
VALIDATOR_SHA256="799e64befca97d4080e03608c80b85dd5a5ecc5f4ae4f35d1116ec2855b9a7c9"

BIS_CONFIG_TAG="release-3.0.21"
BIS_CONFIG_COMMIT="f5d43f6656d6b202eca2edf7cd9180090c1f763b"

EN16931_TAG="validation-1.3.17"
EN16931_COMMIT="d0dea7300c2ad60d50af4a4f31e122fdbf7c0ed3"

XR_CONFIG_TAG="v2026-08-31"
XR_CONFIG_COMMIT="b436fc4bf05ad501ab5cbb4a53fdffee3d4e18be"

MAVEN_CENTRAL="https://repo.maven.apache.org/maven2"
# -----------------------------------------------------------------------------

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$HERE/vendor"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

verify_sha256() { # file expected
  local actual; actual="$(sha256 "$1")"
  if [[ "$actual" != "$2" ]]; then
    echo "ERROR: checksum mismatch for $1" >&2
    echo "  expected $2" >&2
    echo "  actual   $actual" >&2
    exit 1
  fi
  echo "  ok  sha256 $(basename "$1")"
}

clone_pinned() { # url tag commit dest
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$2" "$1" "$4"
  local actual; actual="$(git -C "$4" rev-parse HEAD)"
  if [[ "$actual" != "$3" ]]; then
    echo "ERROR: $1 tag $2 points to $actual, expected $3" >&2
    exit 1
  fi
  echo "  ok  git  $(basename "$1")@$2 ($3)"
}

echo "Preparing $VENDOR"
rm -rf "$VENDOR"
mkdir -p "$VENDOR/repository/resources/ubl/2.1/xsd" \
         "$VENDOR/repository/resources/ubl/2.1/xsl" \
         "$VENDOR/repository/resources/cii/16b/xsd" \
         "$VENDOR/repository/resources/cii/16b/xsl"

echo "1/4 KoSIT validator engine $VALIDATOR_VERSION"
curl -fsSL -o "$VENDOR/validator.jar" \
  "$MAVEN_CENTRAL/org/kosit/validator/$VALIDATOR_VERSION/validator-$VALIDATOR_VERSION-standalone.jar"
verify_sha256 "$VENDOR/validator.jar" "$VALIDATOR_SHA256"

echo "2/4 UBL 2.1 XML Schemas (from KoSIT validator-configuration-bis $BIS_CONFIG_TAG)"
clone_pinned https://github.com/itplr-kosit/validator-configuration-bis \
  "$BIS_CONFIG_TAG" "$BIS_CONFIG_COMMIT" "$TMP/bis"
cp -r "$TMP/bis/resources/ubl/2.1/xsd/." "$VENDOR/repository/resources/ubl/2.1/xsd/"

echo "3/4 EN 16931 rules $EN16931_TAG"
clone_pinned https://github.com/ConnectingEurope/eInvoicing-EN16931 \
  "$EN16931_TAG" "$EN16931_COMMIT" "$TMP/en16931"
cp "$TMP/en16931/ubl/xslt/EN16931-UBL-validation.xslt" \
   "$VENDOR/repository/resources/ubl/2.1/xsl/EN16931-UBL-validation.xsl"
cp "$TMP/en16931/cii/xslt/EN16931-CII-validation.xslt" \
   "$VENDOR/repository/resources/cii/16b/xsl/EN16931-CII-validation.xsl"
cp -r "$TMP/en16931/cii/schema/D16B SCRDM (Subset)/uncoupled clm/CII/uncefact" \
   "$VENDOR/repository/resources/cii/16b/xsd/"
cp "$TMP/en16931/LICENSE.txt" "$VENDOR/LICENSE-EN16931-EUPL-1.2.txt"

echo "4/4 KoSIT report stylesheets $XR_CONFIG_TAG"
clone_pinned https://github.com/itplr-kosit/validator-configuration-xrechnung \
  "$XR_CONFIG_TAG" "$XR_CONFIG_COMMIT" "$TMP/xr"
cp "$TMP/xr/src/default-report.xsl" "$TMP/xr/src/xrechnung-report.xsl" \
   "$VENDOR/repository/resources/"
cp "$TMP/xr/LICENSE" "$VENDOR/LICENSE-KoSIT-Apache-2.0.txt"

# Our own scenario configuration (which rules apply to which document type)
cp "$HERE/config/scenarios.xml" "$VENDOR/repository/scenarios.xml"

echo "Done. Contents:"
( cd "$VENDOR" && du -sh validator.jar repository )
