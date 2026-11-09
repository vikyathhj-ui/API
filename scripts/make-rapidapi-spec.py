"""
Builds docs/rapidapi/openapi.json: an OpenAPI 3.0.3 description of the API for
importing into RapidAPI (RapidAPI adds its own authentication headers, so the
spec contains no security scheme). Run:  python3 scripts/make-rapidapi-spec.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
example = json.loads((ROOT / "service" / "samples" / "fr-consulting.json").read_text(encoding="utf-8"))

s = lambda **kw: {"type": "string", **kw}
dec = lambda d, ex: {"type": "string", "pattern": r"^-?\d+(\.\d+)?$", "description": d, "example": ex}
idref = {"type": "object", "required": ["scheme", "id"],
         "properties": {"scheme": s(description="Identifier scheme (ISO 6523 ICD / EAS code)", example="0002"),
                        "id": s(example="100000009")}}
address = {"type": "object", "required": ["country"], "properties": {
    "line1": s(example="12 rue de l'Exemple"), "line2": s(), "postcode": s(example="75011"),
    "city": s(example="Paris"),
    "country": s(description="ISO 3166-1 alpha-2 country code", pattern="^[A-Za-z]{2}$", example="FR")}}
party = lambda who: {"type": "object", "required": ["name", "address"], "properties": {
    "name": s(example="Atelier Exemple SARL"),
    "vat_id": s(description=f"{who} VAT identifier" + (" (required)" if who == "Seller" else ""),
                example="FR88100000009"),
    "address": address,
    "legal_id": {**idref, "description": "Legal registration ID, e.g. French SIREN with scheme 0002 (required in France)"},
    "electronic_address": {**idref, "description": "Where e-invoices are delivered (required in France)"},
    "email": s(format="email", description="Used as electronic address if electronic_address is not given")}}

invoice_schema = {
    "type": "object", "required": ["invoice", "seller", "buyer", "lines"],
    "description": "Invoice data. Do NOT send totals: line totals, VAT per rate and the amount due are calculated for you.",
    "properties": {
        "invoice": {"type": "object", "required": ["number", "issue_date", "delivery_date"], "properties": {
            "number": s(example="FA-2026-0042"),
            "type": s(enum=["invoice", "credit_note"], default="invoice"),
            "issue_date": s(format="date", example="2026-11-01"),
            "delivery_date": s(format="date", description="Date of delivery or service (legally required in DE/FR)"),
            "due_date": s(format="date", description="Give due_date or payment.terms"),
            "currency": s(default="EUR", example="EUR"),
            "buyer_reference": s(example="PO-7781"),
            "note": s(),
            "notes": {"type": "array", "description": "Coded notes. France requires PMD, PMT and AAB.",
                      "items": {"type": "object", "required": ["text"], "properties": {
                          "subject": s(description="UNTDID 4451 code, e.g. PMD, PMT, AAB", example="PMT"),
                          "text": s(example="Indemnité forfaitaire pour frais de recouvrement : 40 EUR.")}}}}},
        "seller": party("Seller"),
        "buyer": party("Buyer"),
        "payment": {"type": "object", "properties": {
            "means": s(enum=["credit_transfer", "sepa_credit_transfer", "bank_transfer", "direct_debit", "card",
                             "not_defined"], default="credit_transfer"),
            "iban": s(example="FR7630006000011234567890189"), "bic": s(example="AGRIFRPP"),
            "reference": s(), "terms": s(example="Payment within 30 days.")}},
        "lines": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["description", "quantity", "unit_price", "vat_rate"], "properties": {
                "description": s(example="Web development (hours)"),
                "quantity": dec("Quantity", "12.5"),
                "unit": s(default="C62", description="UN/ECE Rec. 20 unit code: C62 piece, HUR hour, DAY day"),
                "unit_price": dec("Net price per unit (not negative)", "85.00"),
                "vat_rate": dec("VAT rate in percent (standard-rated VAT)", "20")}}}},
    "example": example,
}

message = {"type": "object", "properties": {
    "severity": s(enum=["error", "warning", "information"]), "rule": s(nullable=True, example="BR-CO-16"),
    "message": s(), "location": s(nullable=True), "hint": s(description="Plain-English explanation (common rules)")}}
error = {"type": "object", "properties": {"error": {"type": "object", "properties": {
    "code": s(example="invalid_invoice"), "message": s(example="invoice.delivery_date is required"),
    "details": {"type": "object"}}}}}
err = lambda d: {"description": d, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}}

spec = {
    "openapi": "3.0.3",
    "info": {
        "title": "EU E-Invoice API: Factur-X / ZUGFeRD generator & EN 16931 validator",
        "version": "1.0.0",
        "description": (
            "Create and validate EU e-invoices with one call.\n\n"
            "* **POST /v1/invoices**: send simple JSON, get a Factur-X / ZUGFeRD PDF (PDF/A-3 with embedded "
            "EN 16931 XML). Totals and VAT are calculated for you. Output passes veraPDF and Mustang.\n"
            "* **POST /v1/validate**: send UBL/CII XML or a Factur-X/ZUGFeRD PDF; get errors with rule IDs "
            "and plain-English hints.\n\n"
            "Invoice contents are processed in memory and never stored. Technical format generation and "
            "validation only; not tax or legal advice.")},
    "servers": [{"url": "https://api.yourdomain.com", "description": "Replace with your deployed base URL"}],
    "tags": [{"name": "Invoices"}, {"name": "Validation"}],
    "paths": {
        "/v1/invoices": {"post": {
            "tags": ["Invoices"], "operationId": "createInvoice", "summary": "Create a Factur-X / ZUGFeRD e-invoice",
            "description": "Returns a PDF by default. Use format=xml for the CII XML only, or format=json for totals, XML and the PDF (base64).",
            "parameters": [{"name": "format", "in": "query", "required": False,
                            "schema": {"type": "string", "enum": ["pdf", "xml", "json"], "default": "pdf"}}],
            "requestBody": {"required": True, "content": {"application/json": {
                "schema": {"$ref": "#/components/schemas/Invoice"}, "example": example}}},
            "responses": {
                "200": {"description": "The e-invoice", "content": {
                    "application/pdf": {"schema": {"type": "string", "format": "binary"}},
                    "application/xml": {"schema": {"type": "string"}},
                    "application/json": {"schema": {"$ref": "#/components/schemas/InvoiceResult"}}}},
                "400": err("Invoice data incomplete or wrong (message names the field)"),
                "429": err("Rate limit or quota reached")}}},
        "/v1/validate": {"post": {
            "tags": ["Validation"], "operationId": "validateInvoice",
            "summary": "Validate an e-invoice (UBL/CII XML or Factur-X/ZUGFeRD PDF)",
            "description": "Send the raw file as the body. HTTP 200 whenever the document was processed: check `valid`.",
            "requestBody": {"required": True, "content": {
                "application/xml": {"schema": {"type": "string"}},
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
            "responses": {
                "200": {"description": "Validation report", "content": {"application/json": {
                    "schema": {"$ref": "#/components/schemas/ValidationReport"}}}},
                "413": err("File larger than 10 MB"), "415": err("Not XML or PDF"),
                "422": err("PDF without embedded e-invoice XML")}}},
    },
    "components": {"schemas": {
        "Invoice": invoice_schema,
        "InvoiceResult": {"type": "object", "properties": {
            "invoice_number": s(), "profile": s(example="factur-x-en16931"), "currency": s(example="EUR"),
            "totals": {"type": "object", "properties": {k: s(example=v) for k, v in
                       {"net": "1246.49", "vat": "249.30", "gross": "1495.79", "due": "1495.79"}.items()}},
            "vat_breakdown": {"type": "array", "items": {"type": "object", "properties": {
                "rate": s(example="20"), "taxable": s(example="1246.49"), "vat": s(example="249.30")}}},
            "xml": s(description="CII XML"), "pdf_base64": s(format="byte")}},
        "ValidationReport": {"type": "object", "properties": {
            "valid": {"type": "boolean"}, "source": s(enum=["xml", "pdf"]),
            "format": s(nullable=True, example="EN16931 core (CII)"),
            "errors": {"type": "array", "items": message}, "warnings": {"type": "array", "items": message},
            "information": {"type": "array", "items": message}, "ruleset": s(), "limitations": s()}},
        "Error": error}},
}

out = ROOT / "docs" / "rapidapi" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)}")
