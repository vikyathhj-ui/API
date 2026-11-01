"""
Speed test:  python -m app.benchmark [N=50]

Generates the same invoices N times in one process (one CPU core) and reports
median / p95 time per invoice, split into the three steps, for a small invoice
(3-4 lines) and a long one (150 lines, about 6 pages).
"""
import json
import statistics
import sys
import time
import resource
from pathlib import Path

from .facturx_gen import build_cii_xml, make_facturx, parse_invoice, render_pdf

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def long_invoice() -> dict:
    d = json.loads((SAMPLES / "de-mixed-vat.json").read_text(encoding="utf-8"))
    d["lines"] = [{"description": f"Artikel Nr. {i:03d}", "quantity": str(1 + i % 7), "unit": "C62",
                   "unit_price": f"{(i * 1.37) % 97 + 0.99:.2f}", "vat_rate": "19" if i % 3 else "7"}
                  for i in range(150)]
    return d


def run(name: str, data: dict, n: int):
    steps = {"calc+xml": [], "pdf render": [], "embed": [], "total": []}
    for _ in range(n):
        t0 = time.perf_counter()
        inv = parse_invoice(data); xml = build_cii_xml(inv)
        t1 = time.perf_counter()
        pdf = render_pdf(inv)
        t2 = time.perf_counter()
        make_facturx(pdf, xml)
        t3 = time.perf_counter()
        for k, v in zip(steps, (t1 - t0, t2 - t1, t3 - t2, t3 - t0)):
            steps[k].append(v * 1000)
    print(f"{name} (n={n})")
    for k, v in steps.items():
        v.sort()
        print(f"  {k:<11} median {statistics.median(v):7.1f} ms   p95 {v[int(len(v) * 0.95) - 1]:7.1f} ms")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    small = json.loads((SAMPLES / "fr-consulting.json").read_text(encoding="utf-8"))
    run("warm-up", small, 3)
    run("small invoice, 3 lines, 1 page", small, n)
    run("long invoice, 150 lines, ~6 pages", long_invoice(), max(5, n // 5))
    # Peak memory of the whole process (Linux reports KB). Measured AFTER timing,
    # because memory tracers slow Python down and would distort the timings.
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"peak process memory (RSS): {peak_mb:.0f} MB")


if __name__ == "__main__":
    main()
