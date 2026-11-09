# Project Dashboard

_Last updated: 2026-11-09_

| Item | Status |
|---|---|
| **Current phase** | **Phase 9: launch & customer acquisition.** Product v1.0.0 built and tested; waiting on founder: deploy, payments, outreach |
| **Product** | InvoiceFormat API (working name): Factur-X/ZUGFeRD generation + EN 16931 validation API |
| **Decision note** | Founder chose to build before customer interviews (2026-11-09). Interviews now run in parallel, with the live product as demo |
| **Customer validation status** | 0 interviews, 0 pilots (outreach not started) |
| **Active customers** | 0 (only test accounts in the local dev database) |
| **Paying customers** | 0 |
| **API usage (production)** | none: not deployed yet |
| **Revenue** | $0 |
| **Gross margin (actual)** | n/a |
| **Budget spent** | $0 |
| **Estimated monthly operating cost** | ~$10–15 (server, domain, backup storage) + payment fees per sale |
| **Actual monthly operating cost** | $0 |

## Phases
| # | Phase | Status |
|---|---|---|
| 1 | Market research & opportunity discovery | ✅ [report](01-market-research-report.md) |
| 2 | Competitor analysis & scoring | ✅ (report sections 4–6) |
| 3 | Customer validation | ⏳ not started by founder; [kit ready](validation/validation-kit.md) |
| 4 | Product specification & architecture | ✅ (README "What's inside", [API.md](API.md)) |
| 5 | Dockerized MVP development | ✅ v1.0.0 |
| 6 | Testing & benchmarking | ✅ 36 tests, e2e with veraPDF + Mustang, load test |
| 7 | Security & deployment | ✅ hardened containers, HTTPS setup tested locally; ⏳ public deployment needs founder ([DEPLOY.md](DEPLOY.md)) |
| 8 | Pricing & billing | ✅ plans, quotas, usage tracking; ⏳ payment provider account needed ([SELLING.md](SELLING.md)) |
| 9 | Marketplace listing & customer acquisition | ⏳ launch checklist ready ([SELLING.md](SELLING.md)) |
| 10 | Optimization, retention & scaling | later |

## Built and verified (2026-11-09)
- API: generate (PDF/XML/JSON), validate (XML/PDF, plain-English hints), usage, self-service sign-up, health, interactive docs (self-hosted)
- Accounts: hashed API keys, 4 plans (Free 50 / Starter 500 / Growth 5,000 / Scale 30,000 docs per month), per-minute rate limits, monthly quotas, usage log without invoice contents
- Admin command line: create customer, set plan, new/revoke key, list, usage
- Website: landing page with pricing, sign-up form, draft Terms and Privacy
- Production kit: Caddy HTTPS, backup script (restore tested), deploy, operations and selling guides
- Tests: 36/36; e2e 10/10 (veraPDF PDF/A-3b + Mustang zero warnings); 500/500 load-test requests OK; 15/15 clean fresh starts
- Bugs found and fixed during testing: start-up race when two workers created tables; Redis failing under dropped privileges; docs page depending on a blocked CDN; font-cache warnings in read-only containers; e2e script permission issue; benchmark distorted by a memory tracer (earlier)

## RapidAPI (2026-11-09)
- Server integration done and tested (proxy-secret check, per-user usage, 4 new tests, HTTP check)
- OpenAPI 3.0.3 file for import + listing text + pricing: [rapidapi/LISTING.md](rapidapi/LISTING.md)
- Waiting on founder: deploy publicly, create the RapidAPI project, paste the proxy secret, connect PayPal

## Product gaps (prioritise by what prospects ask for)
1. XRechnung (CII/UBL) and Peppol BIS UBL output
2. Reverse charge, VAT exemptions and zero rate; document-level discounts/charges
3. German BR-DE and French BR-FR rule sets in validation
4. Automated billing via payment-provider webhooks
5. Job queue for large batches; customer dashboard

## Founder actions (in order)
- [ ] Pick a final name and domain (check trademark)
- [ ] Rent a server and deploy ([DEPLOY.md](DEPLOY.md)), then run `scripts/e2e-check.sh` against it
- [ ] List on RapidAPI ([rapidapi/LISTING.md](rapidapi/LISTING.md)) and/or open a Merchant-of-Record account for direct sales ([SELLING.md](SELLING.md))
- [ ] Speak to a Chartered Accountant (export of services, GST/LUT)
- [ ] Get the Terms/Privacy drafts reviewed
- [ ] Outreach: 30 messages → 15 conversations → 3 founding customers ([validation kit](validation/validation-kit.md))

## Blockers (only the founder can resolve)
- Public deployment needs your hosting account, domain and approval.
- Payments need your Merchant-of-Record account (identity and bank verification).
- Customer conversations need you.
- Cloud dev environment: a dedicated environment `vikyathhj-ui/API` was created that also allows `deb.debian.org` (needed to build the API image). Docker Hub occasionally rate-limits image downloads there.
