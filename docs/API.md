# API guide (for customers)

Base URL: your deployment, e.g. `https://api.yourdomain.com`. Interactive docs: `/docs`.

## Authentication
Every call except `/v1/signup` and `/v1/health` needs your key:
```
Authorization: Bearer ifk_live_xxxxxxxxxxxxxxxx
```
(`X-API-Key: ifk_live_...` also works.) Get a free key on the home page or via `POST /v1/signup`.

## 1. Create an e-invoice: `POST /v1/invoices`
Send invoice data as JSON. **Do not send totals**: line totals, VAT per rate and the amount due are calculated for you.

`?format=pdf` (default) returns the Factur-X / ZUGFeRD PDF. `?format=xml` returns only the CII XML. `?format=json` returns totals, XML and the PDF (base64) in one object.

```bash
curl -X POST "$BASE/v1/invoices" -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" --data @invoice.json -o invoice.pdf
```

```python
import requests
r = requests.post(f"{BASE}/v1/invoices", json=invoice, headers={"Authorization": f"Bearer {API_KEY}"})
r.raise_for_status()
open("invoice.pdf", "wb").write(r.content)
```

```javascript
const r = await fetch(`${BASE}/v1/invoices?format=json`, {
  method: "POST",
  headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify(invoice),
});
const { totals, xml, pdf_base64 } = await r.json();
```

### Input fields
Send money and quantities as strings (`"85.00"`) for exact decimals. Numbers are accepted too.

| Field | Required | Notes |
|---|---|---|
| `invoice.number` | yes | Your invoice number |
| `invoice.type` | no | `invoice` (default) or `credit_note` |
| `invoice.issue_date` | yes | `YYYY-MM-DD` |
| `invoice.delivery_date` | yes | Date of delivery/service (legally required in DE/FR) |
| `invoice.due_date` | one of due date / `payment.terms` | `YYYY-MM-DD` |
| `invoice.currency` | no | ISO code, default `EUR` |
| `invoice.buyer_reference` | no | Buyer's order or reference |
| `invoice.note` | no | Free text note |
| `invoice.notes[]` | no | `{subject, text}` coded notes. France requires `PMD` (late-payment penalties), `PMT` (€40 recovery fee) and `AAB` (early-payment discount) |
| `seller.name`, `buyer.name` | yes | |
| `seller.vat_id` | yes | e.g. `FR88100000009` |
| `buyer.vat_id` | no | |
| `*.address.line1/line2/postcode/city` | line1 recommended | |
| `*.address.country` | yes | 2 letters, e.g. `DE` |
| `*.legal_id` | FR: yes | `{scheme, id}`; French SIREN uses scheme `0002` |
| `*.electronic_address` | FR: yes | `{scheme, id}`: where e-invoices are delivered; or `email` |
| `payment.means` | no | `credit_transfer` (default), `sepa_credit_transfer`, `bank_transfer`, `direct_debit`, `card`, `not_defined` |
| `payment.iban`, `payment.bic`, `payment.reference`, `payment.terms` | no | |
| `lines[].description` | yes | |
| `lines[].quantity`, `lines[].unit_price` | yes | price must not be negative |
| `lines[].unit` | no | UN/ECE Rec. 20 code: `C62` piece (default), `HUR` hour, `DAY` day |
| `lines[].vat_rate` | yes | e.g. `20`; standard-rated VAT only for now |

A complete example: [`service/samples/fr-consulting.json`](../service/samples/fr-consulting.json).

## 2. Validate an e-invoice: `POST /v1/validate`
Send the raw file (UBL or CII XML, or a Factur-X / ZUGFeRD PDF) as the body.
```bash
curl -X POST "$BASE/v1/validate" -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/pdf" --data-binary @invoice.pdf
```
Response (HTTP 200 whenever the document was processed; check `valid`):
```json
{
  "valid": false,
  "source": "xml",
  "format": "EN16931 core (CII)",
  "errors": [{
    "severity": "error", "rule": "BR-CO-16",
    "message": "[BR-CO-16]-Amount due for payment (BT-115) = Invoice total amount with VAT (BT-112) -Paid amount (BT-113) +Rounding amount (BT-114).",
    "location": "/*:CrossIndustryInvoice[...]",
    "hint": "Amount due must equal: total with VAT - amount already paid + rounding. Usually a rounding or prepayment mistake."
  }],
  "warnings": [], "information": [],
  "ruleset": "EN 16931 core rules (CEN validation artefacts 1.3.17) via KoSIT Validator 1.6.3",
  "limitations": "Checks the European EN 16931 rules. Country-specific extra rules ... are not included yet."
}
```

## 3. Usage: `GET /v1/usage`
Your plan, documents used this calendar month (UTC) and what remains.

## Limits and billing
* One **document** = one successful generation or validation. Requests rejected for bad input are not counted.
* Response headers: `X-Quota-Limit`, `X-Quota-Used`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-Request-ID` (quote this when contacting support).
* Maximum upload: 10 MB.

## Errors
All errors look like `{"error": {"code": "...", "message": "...", "details": {...}}}`. Check `code` in your program.

| HTTP | code | Meaning / what to do |
|---|---|---|
| 400 | `invalid_invoice` | The message says exactly which field is wrong |
| 400 | `invalid_request` | Body isn't valid JSON |
| 400 | `empty_body` | Send the file as the body |
| 401 | `missing_api_key` / `invalid_api_key` | Check the Authorization header / key |
| 409 | `email_already_registered` | Sign-up: this email already has a key |
| 411 | `length_required` | Send a Content-Length header |
| 413 | `payload_too_large` | Max 10 MB |
| 415 | `unsupported_document` | Validate accepts XML or Factur-X/ZUGFeRD PDF |
| 422 | `no_embedded_invoice` | The PDF has no embedded e-invoice XML |
| 429 | `rate_limited` | Wait `Retry-After` seconds |
| 429 | `quota_exceeded` | Monthly quota reached: upgrade or wait for next month |
| 502/503 | `validator_error` / `validator_unavailable` | Temporary: retry later |
| 500 | `internal_error` | Our fault: retry; contact support with the `X-Request-ID` |

## Privacy
Invoice contents are processed in memory and never stored or logged. We store your account, a hash of your key, and a record of each call (endpoint, time, status, duration).

*Technical format generation and validation only; not tax or legal advice.*
