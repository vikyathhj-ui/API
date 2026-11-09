> **Historical spike report (2026-11-01).** This code now lives in `service/` (generator: `service/app/invoice/generator.py`). Commands below refer to the old `sandbox/facturx` layout; to run things today, see the main [README](../README.md).

# Sandbox: Factur-X / ZUGFeRD PDF generation

**What this is:** a feasibility test (a "spike") for the riskiest part of the product: **creating** legally valid hybrid e-invoices, not just checking them. It is *not* the product yet.

**Question we wanted answered:** *Can we turn a simple JSON description of an invoice into a Factur-X / ZUGFeRD PDF that independent, widely used validators accept?*
**Answer: yes.** 3 test invoices (French, German with two VAT rates, a 150-line 6-page one) pass all 4 independent checks with zero errors and zero warnings.

---

## What a Factur-X / ZUGFeRD invoice is (plain language)

It's a normal-looking PDF invoice that a person can read, with a **machine-readable XML file hidden inside it** (attached as `factur-x.xml`). Accounting software reads the XML, so no retyping is needed. France calls it Factur-X, Germany calls it ZUGFeRD; it's the same standard.

```
  your JSON ──▶ 1. check input & CALCULATE totals/VAT ourselves
                        │
                        ├──▶ 2. XML (UN/CEFACT CII, EN 16931 profile)  ──┐
                        │                                                 ├──▶ 4. Factur-X PDF
                        └──▶ 3. printable PDF/A-3b (HTML template) ──────┘     (PDF + XML inside
                                                                                 + metadata)
```

**PDF/A-3** is the archive version of PDF required for e-invoices: all fonts embedded, colours defined, attachments allowed, nothing that can change over time.

## Files

| Path | What it is |
|---|---|
| `app/facturx_gen.py` | The generator: input checks, money maths, XML, PDF, embedding (commented) |
| `app/templates/invoice.html` | The look of the printed invoice (HTML + CSS) |
| `app/cli.py` | Command line: JSON in, PDF + XML out |
| `app/roundtrip.py` | Extracts the XML back out of a PDF and compares it |
| `app/benchmark.py` | Speed test |
| `tests/test_generator.py` | 20 unit tests: rounding, VAT method, bad input, injection attacks |
| `scripts/validate-all.sh` | Runs the 4 independent checks on everything in `out/` |
| `samples/*.json` | Example inputs (fictional companies and numbers) |
| `Dockerfile`, `docker-compose.yml` | Container for the generator (see "Known limitations") |

## The input format (draft of our future API)

See `samples/fr-consulting.json`. The key ideas:
- **You never send totals.** We calculate line totals, VAT per rate and the amount due. This removes the most common cause of rejected e-invoices.
- Send money and quantities as **strings** (`"85.00"`), not JSON numbers, to avoid rounding surprises. Numbers are accepted too.
- `delivery_date` is required. It's legally required on invoices in Germany and France.
- French invoices also need: seller **SIREN** (`legal_id`, scheme `0002`), both parties' **electronic address** (`electronic_address`), and three legal notes (`notes` with subjects `PMD`, `PMT`, `AAB`). Without them, the new French 2026 rules (BR-FR-05/10/12) raise warnings.

## Verified results (2026-11-01, cloud dev environment)

**Independent checks** (`scripts/validate-all.sh`), none of them written by us:

| Check | Tool | fr-consulting | de-mixed-vat | long-150-lines |
|---|---|---|---|---|
| XML inside the PDF identical to generated XML | factur-x library (round trip) | ✅ | ✅ | ✅ |
| EN 16931 business rules on the XML | KoSIT Validator 1.6.3 + CEN rules 1.3.17 (`../validator`) | ✅ 0 messages | ✅ 0 messages | ✅ 0 messages |
| PDF/A-3b archive conformance | veraPDF 1.30.3 (run offline) | ✅ PASS | ✅ PASS | ✅ PASS |
| Full Factur-X check, incl. French 2026 rules | Mustang 2.26.0 (run offline) | ✅ valid, 0 warnings | ✅ valid, 0 warnings | ✅ valid, 0 warnings |

Total: **12/12 checks passed.**

**Checking the checkers:** a plain PDF without embedded XML is correctly rejected by Mustang (missing Factur-X metadata).

**Maths cross-check:** the 150-line invoice's totals were recalculated with a separate script using exact fractions. Identical result: net 28,050.80, VAT 4,183.38, total 32,234.18.

**Unit tests:** 20/20 pass. Two deliberate bugs were planted to prove the tests catch them: wrong rounding direction was caught, and VAT rounded per line instead of per rate was caught.

**What the first validation run found (and we fixed):**
1. An empty delivery section triggered a Peppol warning (R008). Fix: `delivery_date` is now required, which the law demands anyway.
2. The French 2026 rules flagged a missing SIREN, missing buyer e-address and three missing legal notes. Fix: input fields for them. This is a **product insight**: country-specific legal details are exactly what small invoicing tools get wrong, and our API can handle them.
3. A display bug (`20%` printed as `2E+1%`) was found by looking at the rendered PDF, then fixed and covered by a test.

**Speed** (one CPU core, Intel Xeon, after warm-up, `python -m app.benchmark 50`):

| Invoice | median | p95 | where time goes |
|---|---|---|---|
| 3 lines, 1 page | **181 ms** | 233 ms | 95% PDF drawing (WeasyPrint), 3 ms XML, 6 ms embedding |
| 150 lines, 6 pages | **670 ms** | 676 ms | 95% PDF drawing |

Peak memory: ~132 MB. *Business meaning:* one €6/month server core can generate roughly 5 small invoices per second. Generation cost is tiny (well under €0.01 per 1,000 invoices in CPU time), but PDF drawing is ~20× slower than validation. The product will need a job queue for large batches.

## Run it yourself

Needs Docker Desktop. First start the validator from the other sandbox (`cd ../validator`, then `bash scripts/fetch-dependencies.sh` and `docker compose up -d --build`). Then:

```bash
cd sandbox/facturx
```

Build the generator image (installs Python + PDF libraries; a few minutes the first time):

```bash
docker compose build
```

Generate the sample invoices into `out/`:

```bash
docker compose run --rm generator samples/fr-consulting.json samples/de-mixed-vat.json --out out
```

Run the unit tests:

```bash
docker compose run --rm --entrypoint python generator -m unittest -v
```

Run the 4 independent checks:

```bash
bash scripts/validate-all.sh
```

Open `out/fr-consulting.pdf` in any PDF reader. In Adobe Reader, the paperclip icon shows the embedded `factur-x.xml`.

## Known limitations (honest list)

1. **The generator's Docker image was not built in the cloud environment.** It needs Debian packages from `deb.debian.org`, which that environment's network policy blocks. All results above were produced with the **same pinned Python libraries** on Python 3.13 outside Docker. Please run `docker compose build` on your computer and report the result.
2. **Supported now:** standard-rated VAT (category S), any number of rates, invoices and credit notes, bank transfer details. **Not yet:** reverse charge (AE), exempt / zero rate (E/Z), intra-EU (K), invoice-level discounts or charges, prepayments, billing periods, line-level allowances, attachments, other currencies' special cases.
3. **Only the Factur-X EN 16931 profile.** XRechnung-CII and Peppol UBL output are not built yet. The data model is the same, but the rules differ.
4. **French SIREN / e-address scheme:** we used scheme `0225` for the French electronic address, and Mustang accepted it. This must be confirmed against the official French directory rules before production.
5. **On Linux hosts**, the container user (uid 999) may not be allowed to write to `./out`. Docker Desktop on Windows/Mac is not affected. Fix if needed: `sudo chown 999 out`.
6. The visual layout is basic and English-only. Real customers will want their own logo, language and template.

## Licences

factur-x (BSD), drafthorse (Apache 2.0), WeasyPrint (BSD), Jinja2 (BSD). Validators used only for testing: KoSIT (Apache 2.0), veraPDF (GPLv3+/MPLv2+), Mustang (Apache 2.0). DejaVu fonts: free licence (Bitstream Vera derivative).
