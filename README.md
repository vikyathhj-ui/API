# InvoiceFormat API

*(working name, so check the trademark and domain before launch)*

**Create and validate EU e-invoices with one API call.**
Send simple JSON, get back a Factur-X / ZUGFeRD PDF (PDF/A-3 with embedded EN 16931 XML) that passes the independent validators veraPDF and Mustang with zero warnings. Or send any e-invoice (UBL/CII XML or Factur-X PDF) and get its errors explained in plain English.

**Status (2026-11-09):** version 1.0.0 is built, tested and runs in Docker. Not yet deployed publicly (you choose the server and domain, see [docs/DEPLOY.md](docs/DEPLOY.md)). Payments are not yet connected (see [docs/SELLING.md](docs/SELLING.md)).

## Run it on your computer (5 commands)
Needs Docker Desktop (running) and Git. On Windows, use Git Bash.

```bash
cp .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD` to a long random value, then:

```bash
bash scripts/build-images.sh
```

```bash
docker compose up -d
```

Open http://127.0.0.1:8000 (website) and http://127.0.0.1:8000/docs (interactive API docs). Get a key with the form on the website, or:

```bash
docker compose exec api python -m app.admin create --email you@example.com --plan scale
```

Run all tests (36 automated tests, then a full end-to-end check with independent validators):

```bash
docker compose exec api python -m pytest -q -p no:cacheprovider tests/
```

```bash
API_KEY=<your key> bash scripts/e2e-check.sh
```

## What's inside
```
docker-compose.yml        the whole product: api + validator + postgres + redis
service/                  the API (Python, FastAPI)
  app/main.py               endpoints, website, middleware
  app/invoice/generator.py  JSON -> totals -> CII XML -> PDF/A-3 -> Factur-X
  app/validation.py         XML/PDF -> KoSIT validator -> plain-English report
  app/auth.py, limits.py    API keys (hashed), rate limits, monthly quotas, usage log
  app/admin.py              admin command line (customers, keys, plans, usage)
  app/web/                  landing page, terms, privacy (drafts)
  tests/                    36 tests (generator + API integration)
validator/                official KoSIT validator + EN 16931 rules (pinned, checksum-verified)
deploy/                   production: HTTPS via Caddy, backup script
scripts/                  build-images.sh, e2e-check.sh
docs/                     guides (below) and the research behind the product
```

## Guides
| For | Document |
|---|---|
| Customers / developers | [docs/API.md](docs/API.md): endpoints, fields, errors, examples |
| Going live | [docs/DEPLOY.md](docs/DEPLOY.md): server, domain, HTTPS, backups, monitoring |
| Daily running | [docs/OPERATIONS.md](docs/OPERATIONS.md): customers, keys, plans, logs, restore, incidents |
| Selling | [docs/SELLING.md](docs/SELLING.md): payments, launch checklist, first 10 customers |
| RapidAPI marketplace | [docs/rapidapi/LISTING.md](docs/rapidapi/LISTING.md): listing text, pricing, OpenAPI file, setup steps |
| Project status | [docs/PROJECT_DASHBOARD.md](docs/PROJECT_DASHBOARD.md) |
| Background | [market research](docs/01-market-research-report.md) · [Factur-X spike](docs/02-facturx-spike-report.md) · [validation kit](docs/validation/validation-kit.md) |

## Verified on 2026-11-09 (cloud dev environment)
- 40/40 automated tests (incl. RapidAPI marketplace integration): generator maths, input checks, injection attempts, auth, rate limits, quotas, size limits, sign-up, privacy (keys hashed, invoice contents never stored)
- End to end over HTTP: generated PDFs pass **veraPDF (PDF/A-3b)** and **Mustang (Factur-X, incl. French 2026 rules)** with zero warnings, and validate cleanly through the API
- Load test (4 CPU cores, 2 workers): generation ~11 invoices/s, validation ~54/s, 500/500 requests successful
- Production setup tested locally: HTTPS via Caddy, HTTP→HTTPS redirect, HSTS, 12 MB upload rejected at the edge, API port not exposed, real client IPs passed through, forged IP headers ignored
- Clean start-up from an empty database 15 times in a row; backup restored into a scratch database with identical row counts
- All containers run as non-root users with read-only filesystems; only the API (locally) or Caddy (production) is reachable

## Known limitations
- Generation: Factur-X EN 16931 profile with standard-rated VAT only. Not yet: XRechnung/Peppol UBL output, reverse charge, exemptions, document-level discounts/charges.
- Validation: EU EN 16931 core rules. German (BR-DE) and French (BR-FR) national rule sets are not included yet.
- Billing is manual (payment link + admin command). Automate with webhooks later.
- Terms and Privacy pages are drafts and need legal review.
- Technical format generation and validation only; not tax or legal advice.
