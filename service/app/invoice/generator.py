"""
Factur-X / ZUGFeRD generator (sandbox spike).

Pipeline:
    simple JSON  ->  checked & calculated invoice  ->  CII XML (EN 16931 profile)
                                                  ->  human-readable PDF/A-3b
                     PDF/A-3b + XML  ->  Factur-X PDF (XML embedded as factur-x.xml)

Design decisions (deliberate, worth keeping in the product):
  * We CALCULATE every total ourselves from the lines (line net, VAT per rate,
    invoice totals). The caller never sends totals, so arithmetic rules such as
    BR-CO-10..16 cannot fail because of client-side rounding mistakes.
  * Money is handled with Python's Decimal (exact decimal maths), never float.
    float would turn 0.1 + 0.2 into 0.30000000000000004.
  * Rounding: 2 decimals, ROUND_HALF_UP (commercial rounding), per line and per
    VAT group, which is what EN 16931 expects.
  * The HTML template autoescapes all text, so a customer name such as
    "<script>" is printed literally and cannot inject markup into the PDF.

Scope of this spike: standard-rated VAT (category "S") only, one or more rates,
no invoice-level allowances/charges, no reverse charge/exemptions. These are
listed as TODOs in the README.
"""
from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

import facturx
from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.note import IncludedNote
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TWO = Decimal("0.01")
TEMPLATES = Path(__file__).parent / "templates"

# UNTDID 1001 document type codes and UNTDID 4461 payment means codes
DOC_TYPES = {"invoice": "380", "credit_note": "381"}
PAYMENT_MEANS = {"credit_transfer": "58", "sepa_credit_transfer": "58", "bank_transfer": "30",
                 "direct_debit": "59", "card": "48", "not_defined": "1"}


class InvoiceInputError(ValueError):
    """Raised when the JSON input is incomplete or wrong. Message is user-facing."""


def money(value: Decimal) -> Decimal:
    return value.quantize(TWO, rounding=ROUND_HALF_UP)


def _dec(value, where: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InvoiceInputError(f"{where}: '{value}' is not a number")
    if not d.is_finite():
        raise InvoiceInputError(f"{where}: '{value}' is not a finite number")
    return d


def _date(value, where: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        raise InvoiceInputError(f"{where}: '{value}' is not a date in YYYY-MM-DD format")


def _req(obj: dict, key: str, where: str):
    v = obj.get(key)
    if v is None or (isinstance(v, str) and not v.strip()):
        raise InvoiceInputError(f"{where}.{key} is required")
    return v


# --------------------------------------------------------------------------- #
# 1. Input model + calculation
# --------------------------------------------------------------------------- #
@dataclass
class Line:
    number: int
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    vat_rate: Decimal
    net: Decimal = Decimal("0")


@dataclass
class VatGroup:
    rate: Decimal
    basis: Decimal
    tax: Decimal


@dataclass
class Invoice:
    raw: dict
    number: str
    type_code: str
    issue_date: dt.date
    due_date: dt.date | None
    delivery_date: dt.date
    currency: str
    buyer_reference: str | None
    note: str | None
    notes: list[dict]
    seller: dict
    buyer: dict
    payment: dict
    lines: list[Line]
    vat_groups: list[VatGroup] = field(default_factory=list)
    line_total: Decimal = Decimal("0")
    tax_total: Decimal = Decimal("0")
    grand_total: Decimal = Decimal("0")
    due_amount: Decimal = Decimal("0")


def _party(p: dict, where: str) -> dict:
    _req(p, "name", where)
    addr = _req(p, "address", where)
    country = str(_req(addr, "country", f"{where}.address")).upper()
    if len(country) != 2 or not country.isalpha():
        raise InvoiceInputError(f"{where}.address.country must be a 2-letter ISO code like 'FR'")
    for key in ("legal_id", "electronic_address"):
        if p.get(key) is not None:
            _req(p[key], "scheme", f"{where}.{key}")
            _req(p[key], "id", f"{where}.{key}")
    return p


def _notes(raw: list) -> list[dict]:
    """Coded notes, e.g. French mandatory mentions: PMD (late-payment penalties),
    PMT (EUR 40 recovery fee), AAB (early-payment discount). Codes: UNTDID 4451."""
    if not isinstance(raw, list):
        raise InvoiceInputError("invoice.notes must be a list of {subject, text}")
    out = []
    for i, n in enumerate(raw):
        text = _req(n, "text", f"invoice.notes[{i}]")
        out.append({"subject": n.get("subject"), "text": str(text)})
    return out


def parse_invoice(data: dict) -> Invoice:
    """Check the JSON input and calculate all amounts. Raises InvoiceInputError."""
    inv = _req(data, "invoice", "root")
    seller = _party(_req(data, "seller", "root"), "seller")
    buyer = _party(_req(data, "buyer", "root"), "buyer")
    if not seller.get("vat_id"):
        raise InvoiceInputError("seller.vat_id is required for standard-rated VAT (rule BR-S-02)")
    doc_type = inv.get("type", "invoice")
    if doc_type not in DOC_TYPES:
        raise InvoiceInputError(f"invoice.type must be one of {sorted(DOC_TYPES)}")
    payment = data.get("payment") or {}
    means = payment.get("means", "credit_transfer")
    if means not in PAYMENT_MEANS:
        raise InvoiceInputError(f"payment.means must be one of {sorted(PAYMENT_MEANS)}")

    raw_lines = _req(data, "lines", "root")
    if not isinstance(raw_lines, list) or not raw_lines:
        raise InvoiceInputError("lines must be a non-empty list")
    lines = []
    for i, l in enumerate(raw_lines, start=1):
        w = f"lines[{i - 1}]"
        q = _dec(_req(l, "quantity", w), f"{w}.quantity")
        price = _dec(_req(l, "unit_price", w), f"{w}.unit_price")
        rate = _dec(_req(l, "vat_rate", w), f"{w}.vat_rate")
        if price < 0:
            raise InvoiceInputError(f"{w}.unit_price must not be negative (BR-27)")
        if not (Decimal("0") < rate < Decimal("100")):
            raise InvoiceInputError(f"{w}.vat_rate must be between 0 and 100 (only standard rates supported in this spike)")
        line = Line(i, str(_req(l, "description", w)), q, str(l.get("unit", "C62")), price, rate)
        line.net = money(q * price)
        lines.append(line)

    invoice = Invoice(
        raw=data,
        number=str(_req(inv, "number", "invoice")),
        type_code=DOC_TYPES[doc_type],
        issue_date=_date(_req(inv, "issue_date", "invoice"), "invoice.issue_date"),
        due_date=_date(inv["due_date"], "invoice.due_date") if inv.get("due_date") else None,
        # Delivery / service date: legally required on invoices in DE (§14 UStG) and FR,
        # and it avoids an empty <ApplicableHeaderTradeDelivery/> (PEPPOL-EN16931-R008).
        delivery_date=_date(_req(inv, "delivery_date", "invoice"), "invoice.delivery_date"),
        currency=str(inv.get("currency", "EUR")).upper(),
        buyer_reference=inv.get("buyer_reference"),
        note=inv.get("note"),
        notes=_notes(inv.get("notes") or []),
        seller=seller, buyer=buyer, payment=payment, lines=lines,
    )

    # VAT is calculated per rate on the SUM of line nets (EN 16931 method)
    groups: dict[Decimal, Decimal] = {}
    for line in lines:
        groups[line.vat_rate] = groups.get(line.vat_rate, Decimal("0")) + line.net
    invoice.vat_groups = [VatGroup(r, money(b), money(b * r / Decimal(100)))
                          for r, b in sorted(groups.items())]
    invoice.line_total = money(sum((l.net for l in lines), Decimal("0")))
    invoice.tax_total = money(sum((g.tax for g in invoice.vat_groups), Decimal("0")))
    invoice.grand_total = invoice.line_total + invoice.tax_total
    invoice.due_amount = invoice.grand_total  # no prepayment in this spike
    if invoice.due_amount > 0 and not invoice.due_date and not payment.get("terms"):
        raise InvoiceInputError("give invoice.due_date or payment.terms (rule BR-CO-25)")
    return invoice


# --------------------------------------------------------------------------- #
# 2. CII XML (Factur-X EN16931 profile)
# --------------------------------------------------------------------------- #
def _fill_party(party, p: dict, with_vat: bool):
    party.name = p["name"]
    a = p["address"]
    party.address.line_one = a.get("line1")
    if a.get("line2"):
        party.address.line_two = a["line2"]
    party.address.postcode = a.get("postcode")
    party.address.city_name = a.get("city")
    party.address.country_id = a["country"].upper()
    if p.get("legal_id"):  # BT-30 / BT-47, e.g. French SIREN = scheme 0002
        party.legal_organization.id = (str(p["legal_id"]["scheme"]), str(p["legal_id"]["id"]))
    if p.get("electronic_address"):  # BT-34 / BT-49, where e-invoices are delivered
        ea = p["electronic_address"]
        party.electronic_address.uri_ID = (str(ea["scheme"]), str(ea["id"]))
    elif p.get("email"):
        party.electronic_address.uri_ID = ("EM", p["email"])
    if with_vat and p.get("vat_id"):
        party.tax_registrations.add(TaxRegistration(id=("VA", p["vat_id"])))


def build_cii_xml(inv: Invoice) -> bytes:
    doc = Document()
    doc.context.guideline_parameter.id = "urn:cen.eu:en16931:2017"  # = Factur-X EN16931 profile
    doc.header.id = inv.number
    doc.header.type_code = inv.type_code
    doc.header.issue_date_time = inv.issue_date
    if inv.note:
        doc.header.notes.add(IncludedNote(content=inv.note))
    for n in inv.notes:
        note = IncludedNote(content=n["text"])
        if n["subject"]:
            note.subject_code = n["subject"]
        doc.header.notes.add(note)

    agr = doc.trade.agreement
    if inv.buyer_reference:
        agr.buyer_reference = inv.buyer_reference
    _fill_party(agr.seller, inv.seller, with_vat=True)
    _fill_party(agr.buyer, inv.buyer, with_vat=True)

    doc.trade.delivery.event.occurrence = inv.delivery_date

    st = doc.trade.settlement
    st.currency_code = inv.currency
    pm = PaymentMeans()
    pm.type_code = PAYMENT_MEANS[inv.payment.get("means", "credit_transfer")]
    if inv.payment.get("iban"):
        pm.payee_account.iban = inv.payment["iban"].replace(" ", "")
    if inv.payment.get("bic"):
        pm.payee_institution.bic = inv.payment["bic"]
    st.payment_means.add(pm)
    if inv.payment.get("reference"):
        st.payment_reference = inv.payment["reference"]

    for line in inv.lines:
        li = LineItem()
        li.document.line_id = str(line.number)
        li.product.name = line.description
        li.agreement.net.amount = line.unit_price
        li.delivery.billed_quantity = (line.quantity, line.unit)
        li.settlement.trade_tax.type_code = "VAT"
        li.settlement.trade_tax.category_code = "S"
        li.settlement.trade_tax.rate_applicable_percent = line.vat_rate
        li.settlement.monetary_summation.total_amount = line.net
        doc.trade.items.add(li)

    for g in inv.vat_groups:
        t = ApplicableTradeTax()
        t.calculated_amount = g.tax
        t.basis_amount = g.basis
        t.type_code = "VAT"
        t.category_code = "S"
        t.rate_applicable_percent = g.rate
        st.trade_tax.add(t)

    if inv.due_date or inv.payment.get("terms"):
        terms = PaymentTerms()
        if inv.payment.get("terms"):
            terms.description = inv.payment["terms"]
        if inv.due_date:
            terms.due = inv.due_date
        st.terms.add(terms)

    ms = st.monetary_summation
    ms.line_total = inv.line_total
    ms.charge_total = Decimal("0.00")
    ms.allowance_total = Decimal("0.00")
    ms.tax_basis_total = (inv.line_total, None)
    ms.tax_total = (inv.tax_total, inv.currency)
    ms.grand_total = (inv.grand_total, None)
    ms.due_amount = inv.due_amount

    return doc.serialize(schema="FACTUR-X_EN16931")


# --------------------------------------------------------------------------- #
# 3. Human-readable PDF/A-3b
# --------------------------------------------------------------------------- #
_env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))


def _fmt(d: Decimal) -> str:
    return f"{d:,.2f}"


def _pct(d: Decimal) -> str:
    """20 -> '20', 5.50 -> '5.5' (never scientific notation like '2E+1')."""
    return format(d.normalize(), "f")


def render_pdf(inv: Invoice) -> bytes:
    html = _env.get_template("invoice.html").render(inv=inv, fmt=_fmt, pct=_pct)
    return HTML(string=html, base_url=str(TEMPLATES)).write_pdf(pdf_variant="pdf/a-3b")


# --------------------------------------------------------------------------- #
# 4. Combine: Factur-X = PDF/A-3 + embedded factur-x.xml + XMP metadata
# --------------------------------------------------------------------------- #
def make_facturx(pdf: bytes, xml: bytes, lang: str = "en-GB") -> bytes:
    return facturx.generate_from_binary(
        pdf, xml, flavor="factur-x", level="en16931", check_xsd=True, lang=lang)


def generate(data: dict) -> tuple[bytes, bytes, Invoice]:
    """JSON dict -> (factur-x pdf bytes, xml bytes, calculated invoice)."""
    inv = parse_invoice(data)
    xml = build_cii_xml(inv)
    pdf = make_facturx(render_pdf(inv), xml)
    return pdf, xml, inv


def extract_xml(pdf: bytes) -> bytes:
    """Read the embedded XML back out of a Factur-X PDF (round-trip check)."""
    filename, xml = facturx.get_xml_from_pdf(io.BytesIO(pdf), check_xsd=False)
    return xml
