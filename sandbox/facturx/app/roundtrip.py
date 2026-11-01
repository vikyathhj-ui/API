"""
Round-trip check:  python -m app.roundtrip <invoice.pdf> <expected.xml>

Extracts the embedded factur-x.xml from the PDF (the way a customer's
accounting software would) and checks it is byte-identical to the XML we
generated. Exit code 0 = identical, 1 = different or missing.
"""
import sys
from pathlib import Path

from .facturx_gen import extract_xml


def main() -> int:
    pdf, expected = Path(sys.argv[1]), Path(sys.argv[2])
    embedded = extract_xml(pdf.read_bytes())
    if embedded == expected.read_bytes():
        print(f"identical ({len(embedded)} bytes)")
        return 0
    print("DIFFERENT" if embedded else "MISSING")
    return 1


if __name__ == "__main__":
    sys.exit(main())
