"""
Command line:  python -m app.cli <invoice.json> [<invoice2.json> ...] --out <folder>

For each JSON file writes <name>.pdf (Factur-X) and <name>.xml (the embedded XML)
and prints the calculated totals and how long generation took.
Exit code 1 if any input was rejected.
"""
import argparse
import json
import sys
import time
from pathlib import Path

from .facturx_gen import InvoiceInputError, _pct, generate


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Factur-X PDFs from JSON")
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=Path("out"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    failed = 0
    for path in args.inputs:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            t0 = time.perf_counter()
            pdf, xml, inv = generate(data)
            ms = (time.perf_counter() - t0) * 1000
        except InvoiceInputError as e:
            print(f"REJECTED {path.name}: {e}")
            failed += 1
            continue
        (args.out / f"{path.stem}.pdf").write_bytes(pdf)
        (args.out / f"{path.stem}.xml").write_bytes(xml)
        vat = ", ".join(f"{_pct(g.rate)}%: {g.tax}" for g in inv.vat_groups)
        print(f"OK       {path.name}: net {inv.line_total} + VAT {inv.tax_total} ({vat}) "
              f"= {inv.grand_total} {inv.currency}  | {len(pdf) // 1024} KB PDF in {ms:.0f} ms")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
