"""
Validation: XML or Factur-X/ZUGFeRD PDF in, clear JSON report out.

1. Detect the input: a PDF (we pull out the embedded XML) or XML.
2. Send the XML to the official KoSIT validator (internal container, never public).
3. Turn its XML report into simple JSON, adding plain-English hints for the
   most common errors (our differentiator: errors developers can understand).
"""
import io
import logging

import facturx
import httpx
from lxml import etree

from .config import settings
from .errors import APIError

log = logging.getLogger("app.validation")
NS = {"rep": "http://www.xoev.de/de/validator/varl/1",
      "s": "http://www.xoev.de/de/validator/framework/1/scenarios"}

RULESET = "EN 16931 core rules (CEN validation artefacts 1.3.17) via KoSIT Validator 1.6.3"
LIMITATIONS = ("Checks the European EN 16931 rules. Country-specific extra rules "
               "(German XRechnung BR-DE-*, French BR-FR-*) are not included yet.")

# Plain-English explanations for the errors people hit most often.
HINTS = {
    "BR-01": "Add the specification identifier (Factur-X/CII: GuidelineSpecifiedDocumentContextParameter/ID; UBL: CustomizationID).",
    "BR-02": "The invoice number is missing.",
    "BR-03": "The invoice issue date is missing.",
    "BR-04": "The invoice type code is missing (380 = invoice, 381 = credit note).",
    "BR-05": "The invoice currency code is missing (e.g. EUR).",
    "BR-06": "The seller's name is missing.",
    "BR-07": "The buyer's name is missing.",
    "BR-08": "The seller's postal address is missing.",
    "BR-09": "The seller's country code is missing (2 letters, e.g. DE).",
    "BR-10": "The buyer's postal address is missing.",
    "BR-11": "The buyer's country code is missing (2 letters, e.g. FR).",
    "BR-16": "An invoice needs at least one line item.",
    "BR-CO-10": "The sum of all line net amounts does not equal the invoice's total net amount. Recalculate the total from the lines.",
    "BR-CO-13": "Invoice total without VAT must equal: sum of line net amounts - document allowances + document charges.",
    "BR-CO-14": "Total VAT must equal the sum of the VAT amounts of each VAT rate group.",
    "BR-CO-15": "Invoice total with VAT must equal: total without VAT + total VAT.",
    "BR-CO-16": "Amount due must equal: total with VAT - amount already paid + rounding. Usually a rounding or prepayment mistake.",
    "BR-CO-25": "When an amount is due, give either a payment due date or payment terms.",
    "BR-S-02": "Standard-rated VAT needs the seller's VAT ID (or tax registration / tax representative).",
    "BR-S-08": "For each VAT rate, the taxable amount must equal the sum of the line net amounts at that rate (plus charges, minus allowances). Usually a rounding mistake.",
    "BR-S-09": "VAT amount for a rate must equal taxable amount x rate, rounded to 2 decimals.",
    "BR-CL-23": "Unit of measure must be a UN/ECE Recommendation 20 code (e.g. C62 = piece, HUR = hour, DAY = day).",
}


def extract_xml(body: bytes) -> tuple[bytes, str]:
    """Returns (xml bytes, source) where source is 'pdf' or 'xml'."""
    head = body[:1024].lstrip(b"\xef\xbb\xbf \t\r\n")
    if body.startswith(b"%PDF-"):
        try:
            _, xml = facturx.get_xml_from_pdf(io.BytesIO(body), check_xsd=False)
        except Exception:
            xml = None
        if not xml:
            raise APIError(422, "no_embedded_invoice",
                           "This PDF does not contain an embedded Factur-X / ZUGFeRD XML invoice.")
        return xml, "pdf"
    if head.startswith(b"<"):
        return body, "xml"
    raise APIError(415, "unsupported_document",
                   "Send an XML e-invoice (UBL or CII) or a Factur-X / ZUGFeRD PDF.")


def _parse_report(report: bytes) -> dict:
    root = etree.fromstring(report)
    scenario = root.findtext("rep:scenarioMatched/s:scenario/s:name", namespaces=NS)
    messages = []
    for m in root.iterfind(".//rep:message", NS):
        code = m.get("code")
        item = {"severity": m.get("level", "error"),
                "rule": code,
                "message": " ".join((m.text or "").split()),
                "location": m.get("xpathLocation")}
        if m.get("lineNumber"):
            item["line"] = int(m.get("lineNumber"))
        if code in HINTS:
            item["hint"] = HINTS[code]
        messages.append(item)
    errors = [m for m in messages if m["severity"] == "error"]
    warnings = [m for m in messages if m["severity"] == "warning"]
    info = [m for m in messages if m["severity"] not in ("error", "warning")]
    if scenario is None:
        errors.insert(0, {"severity": "error", "rule": None,
                          "message": "Not recognised as an EN 16931 invoice (UBL Invoice/CreditNote or "
                                     "UN/CEFACT CII with an urn:cen.eu:en16931:2017 specification ID).",
                          "location": None,
                          "hint": "Check the document type and the specification identifier (BT-24)."})
    return {"valid": root.get("valid") == "true" and scenario is not None,
            "format": scenario, "errors": errors, "warnings": warnings, "information": info}


def validate_xml(xml: bytes) -> dict:
    try:
        resp = httpx.post(f"{settings.validator_url}/invoice.xml", content=xml,
                          headers={"Content-Type": "application/xml"}, timeout=60)
    except httpx.HTTPError:
        log.exception("validator unreachable")
        raise APIError(503, "validator_unavailable", "The validation engine is temporarily unavailable. "
                       "Please retry in a minute.", headers={"Retry-After": "30"})
    if resp.status_code == 422:
        # The engine could not process the document at all, typically XML that is not well-formed.
        detail = ""
        try:
            detail = " ".join(etree.fromstring(resp.content).itertext())[:500]
        except Exception:
            pass
        return {"valid": False, "format": None, "warnings": [], "information": [],
                "errors": [{"severity": "error", "rule": None, "location": None,
                            "message": "The document could not be read as XML. " + detail.strip(),
                            "hint": "Check that the file is complete, well-formed XML in UTF-8."}]}
    if resp.status_code not in (200, 406):
        log.error("validator returned HTTP %s", resp.status_code)
        raise APIError(502, "validator_error", "The validation engine returned an unexpected error.")
    report = _parse_report(resp.content)
    report["ruleset"] = RULESET
    report["limitations"] = LIMITATIONS
    return report


def validator_healthy() -> bool:
    try:
        return httpx.get(f"{settings.validator_url}/server/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False
