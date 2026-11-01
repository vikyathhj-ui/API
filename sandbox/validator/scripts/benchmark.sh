#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# benchmark.sh: measures how fast the validator answers.
#
# Sends the same valid invoice N times, first one-by-one (latency), then
# with C requests at once (throughput). Prints min / median / p95 / max.
#
# Usage:  bash scripts/benchmark.sh [N=200] [C=4]
# -----------------------------------------------------------------------------
set -euo pipefail
N="${1:-200}"; C="${2:-4}"
URL="${VALIDATOR_URL:-http://127.0.0.1:8080}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$HERE/samples/valid/xrechnung-ubl-invoice.xml"

one() { curl -sS -o /dev/null -w '%{time_total}\n' -X POST -H 'Content-Type: application/xml' \
          --data-binary "@$FILE" "$URL/bench.xml"; }
export -f one; export FILE URL

stats() { sort -n | awk '{a[NR]=$1} END {printf "  n=%d  min=%.0fms  median=%.0fms  p95=%.0fms  max=%.0fms\n", NR, a[1]*1000, a[int(NR*0.5)]*1000, a[int(NR*0.95)]*1000, a[NR]*1000}'; }

echo "Warm-up (20 requests, Java gets faster after the first few)..."
for _ in $(seq 20); do one > /dev/null; done

echo "Sequential latency, $N requests:"
for _ in $(seq "$N"); do one; done | stats

echo "Concurrent, $N requests with $C at a time:"
start=$(date +%s.%N)
seq "$N" | xargs -P "$C" -I{} bash -c one | stats
end=$(date +%s.%N)
awk -v n="$N" -v s="$start" -v e="$end" 'BEGIN {printf "  throughput = %.1f invoices/second\n", n/(e-s)}'
