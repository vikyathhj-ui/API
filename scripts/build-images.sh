#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Build the Docker images. On a normal computer this is the same as
# `docker compose build`. Behind a proxy that inspects HTTPS (corporate networks,
# some cloud dev environments) set:
#     BUILD_CA_FILE=/path/to/proxy-ca.crt   (the proxy's certificate bundle)
# and the usual HTTPS_PROXY / NO_PROXY variables. They are used only during the
# build and are not stored in the images.
# -----------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

args=()
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  args+=(--network host --build-arg "HTTPS_PROXY=$HTTPS_PROXY" --build-arg "https_proxy=$HTTPS_PROXY"
         --build-arg "NO_PROXY=${NO_PROXY:-}" --build-arg "no_proxy=${NO_PROXY:-}")
fi
if [[ -n "${BUILD_CA_FILE:-}" ]]; then
  args+=(--secret "id=build_ca,src=$BUILD_CA_FILE")
fi

[[ -f validator/vendor/validator.jar ]] || bash validator/scripts/fetch-dependencies.sh
docker build "${args[@]}" -t invoiceformat/api:1.0.0 service/
docker build -t invoiceformat/validator:1.6.3-en16931-1.3.17 validator/
echo "Images built. Start with: docker compose up -d"
