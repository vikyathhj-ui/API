"""
Unit tests for the Factur-X generator.  Run:  python -m unittest -v

What we test and why:
  * money maths: rounding and the VAT-per-rate method (the #1 cause of rejected invoices)
  * input checking: bad input must give a clear, user-facing error, never a crash
  * injection: customer text must never break the XML or the PDF's HTML
"""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from lxml import etree

from app.facturx_gen import (InvoiceInputError, _env, _fmt, _pct, build_cii_xml,
                             extract_xml, generate, parse_invoice)

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
NS = {"rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
      "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"}


def base():
    return json.loads((SAMPLES / "de-mixed-vat.json").read_text(encoding="utf-8"))


def with_lines(*lines):
    d = base()
    d["lines"] = [dict(description="x", quantity=q, unit_price=p, vat_rate=r) for q, p, r in lines]
    return d


class MoneyMaths(unittest.TestCase):
    def test_line_net_rounds_half_up(self):
        inv = parse_invoice(with_lines(("1", "0.005", "19"), ("3", "11.333", "19")))
        self.assertEqual([l.net for l in inv.lines], [Decimal("0.01"), Decimal("34.00")])

    def test_vat_is_calculated_per_rate_on_the_sum_not_per_line(self):
        # per line: 1.05 * 7% = 0.0735 -> 0.07, x3 = 0.21 (WRONG method)
        # per rate: 3.15 * 7% = 0.2205 -> 0.22            (EN 16931 method)
        inv = parse_invoice(with_lines(("1", "1.05", "7"), ("1", "1.05", "7"), ("1", "1.05", "7")))
        self.assertEqual(inv.tax_total, Decimal("0.22"))

    def test_mixed_rates_totals(self):
        inv = parse_invoice(base())
        self.assertEqual((inv.line_total, inv.tax_total, inv.grand_total),
                         (Decimal("1074.53"), Decimal("182.61"), Decimal("1257.14")))
        self.assertEqual([(g.rate, g.basis, g.tax) for g in inv.vat_groups],
                         [(Decimal("7"), Decimal("179.58"), Decimal("12.57")),
                          (Decimal("19"), Decimal("894.95"), Decimal("170.04"))])

    def test_json_numbers_are_accepted_without_float_errors(self):
        inv = parse_invoice(with_lines((0.1, 0.2, 19)))  # numbers, not strings
        self.assertEqual(inv.lines[0].net, Decimal("0.02"))

    def test_display_formatting(self):
        self.assertEqual(_pct(Decimal("20")), "20")      # not '2E+1'
        self.assertEqual(_pct(Decimal("5.50")), "5.5")
        self.assertEqual(_fmt(Decimal("1257.14")), "1,257.14")


class InputChecking(unittest.TestCase):
    def assertRejected(self, data, fragment):
        with self.assertRaises(InvoiceInputError) as ctx:
            parse_invoice(data)
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_delivery_date(self):
        d = base(); del d["invoice"]["delivery_date"]
        self.assertRejected(d, "invoice.delivery_date is required")

    def test_missing_seller_vat_id(self):
        d = base(); del d["seller"]["vat_id"]
        self.assertRejected(d, "BR-S-02")

    def test_bad_country(self):
        d = base(); d["buyer"]["address"]["country"] = "Germany"
        self.assertRejected(d, "2-letter ISO code")

    def test_not_a_number(self):
        self.assertRejected(with_lines(("abc", "1", "19")), "lines[0].quantity: 'abc' is not a number")

    def test_infinity_and_nan(self):
        self.assertRejected(with_lines(("Infinity", "1", "19")), "not a finite number")
        self.assertRejected(with_lines(("1", "NaN", "19")), "not a finite number")

    def test_negative_price(self):
        self.assertRejected(with_lines(("1", "-5", "19")), "BR-27")

    def test_zero_rate_not_supported_yet(self):
        self.assertRejected(with_lines(("1", "5", "0")), "vat_rate")

    def test_bad_date(self):
        d = base(); d["invoice"]["issue_date"] = "01/11/2026"
        self.assertRejected(d, "YYYY-MM-DD")

    def test_no_lines(self):
        d = base(); d["lines"] = []
        self.assertRejected(d, "non-empty list")

    def test_needs_due_date_or_terms(self):
        d = base(); d["payment"].pop("terms")
        self.assertRejected(d, "BR-CO-25")

    def test_unknown_payment_means(self):
        d = base(); d["payment"]["means"] = "bitcoin"
        self.assertRejected(d, "payment.means")


class Injection(unittest.TestCase):
    EVIL = '</ram:Name><ram:Evil>x</ram:Evil> & <script>alert(1)</script>'

    def test_xml_stays_well_formed_and_text_is_preserved(self):
        d = base(); d["seller"]["name"] = self.EVIL
        root = etree.fromstring(build_cii_xml(parse_invoice(d)))
        name = root.find(".//ram:SellerTradeParty/ram:Name", NS).text
        self.assertEqual(name, self.EVIL)
        self.assertIsNone(root.find(".//ram:Evil", NS))

    def test_html_is_escaped(self):
        d = base(); d["lines"][0]["description"] = self.EVIL
        html = _env.get_template("invoice.html").render(inv=parse_invoice(d), fmt=_fmt, pct=_pct)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class EndToEnd(unittest.TestCase):
    def test_generate_and_round_trip(self):
        pdf, xml, inv = generate(base())
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertEqual(extract_xml(pdf), xml)
        root = etree.fromstring(xml)
        self.assertEqual(root.find(".//ram:GuidelineSpecifiedDocumentContextParameter/ram:ID", NS).text,
                         "urn:cen.eu:en16931:2017")
        self.assertEqual(root.find(".//ram:DuePayableAmount", NS).text, "1257.14")

    def test_input_is_not_modified(self):
        d = base(); before = copy.deepcopy(d)
        generate(d)
        self.assertEqual(d, before)


if __name__ == "__main__":
    unittest.main()
