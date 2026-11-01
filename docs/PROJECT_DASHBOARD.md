# Project Dashboard

_Last updated: 2026-11-01_

| Item | Status |
|---|---|
| **Current phase** | **Phase 3: Customer validation** (founder approved direction 2026-11-01). Technical feasibility spike done in parallel |
| **Current product decision** | **Approved for validation:** EU e-invoice generation + validation API (score 72/100). Fallbacks: template→PDF API (65), cron monitoring (62.5). Parallel low-cost test: component datasheet intelligence (59) |
| **Technical feasibility** | ✅ **Validation:** official KoSIT validator + EN 16931 rules in Docker; 66/66 official test invoices pass; median 10 ms. See [sandbox/validator](../sandbox/validator/README.md) |
| | ✅ **Generation:** JSON → Factur-X/ZUGFeRD PDF passes KoSIT, veraPDF (PDF/A-3b) and Mustang (incl. French 2026 rules) with 0 warnings; ~180 ms per 1-page invoice. See [sandbox/facturx](../sandbox/facturx/README.md) |
| **Customer validation status** | Not started. 0 interviews, 0 pilots, 0 waitlist |
| **Active customers** | 0 |
| **Paying customers** | 0 |
| **API usage** | 0 (nothing built) |
| **Revenue** | $0 |
| **Gross margin (actual)** | n/a |
| **Budget spent** | $0 |
| **Estimated monthly operating cost (after launch)** | ~$15–40 (estimate) |
| **Actual monthly operating cost** | $0 |

## Phases
| # | Phase | Status |
|---|---|---|
| 1 | Market research & opportunity discovery | ✅ Done — see [01-market-research-report.md](01-market-research-report.md) |
| 2 | Competitor analysis & scoring | ✅ Done (in the Phase 1 report, Sections 4–6) |
| 3 | Customer validation | ⏳ **In progress (founder's outreach)**: kit ready in [validation/validation-kit.md](validation/validation-kit.md) |
| 4 | Product specification & architecture | Not started (only after GO) |
| 5 | Dockerized MVP development | Not started |
| 6 | Testing & benchmarking | Not started |
| 7 | Security & deployment | Not started |
| 8 | Pricing & billing | Hypothesis only (report Section 7) |
| 9 | Marketplace listing & customer acquisition | Not started |
| 10 | Optimization, retention & scaling | Not started |

## Completed
- Researched 28 API opportunities across AI, data, developer, semiconductor and business-automation categories
- Scored 12 shortlisted ideas with the weighted framework; arithmetic verified
- Unit economics, three scenarios and break-even for the leading candidate
- Risk register
- Validation kit (interview script, survey, landing copy, outreach templates, prospect-finding recipes)
- Docker sandbox: official KoSIT validator 1.6.3 + EN 16931 rules 1.3.17, pinned and checksum-verified, non-root, read-only container
- Tests: 6/6 sandbox tests; 66/66 official XRechnung standard invoices accepted; malformed/XXE/oversized inputs handled safely
- Benchmark: median 10 ms per validation, ~87 docs/s on 1 CPU, ~205 MB RAM
- Factur-X generation spike: JSON → CII XML → PDF/A-3b → Factur-X; 12/12 independent checks (round-trip, KoSIT, veraPDF, Mustang); 20/20 unit tests incl. 2 planted-bug checks; totals independently re-verified
- Benchmark: 181 ms median per 1-page invoice, 670 ms per 6-page invoice, ~132 MB RAM (95% of time is PDF drawing)

## Learned from the sandbox (affects Phase 4 design)
- Each country variant (XRechnung standard/extension/CVD, Peppol, Factur-X) needs its own rule profile and severity overrides; generic EN 16931 is too strict for some German variants.
- German BR-DE rules must still be added (official host blocked in the cloud environment; should work on a local machine).
- The validator has no authentication and no size limit, so our API layer must add keys, rate limits and a max upload size.
- **We should calculate totals/VAT ourselves** and never accept client totals; this removes the most common rejection cause and is a selling point.
- **France's 2026 rules add mandatory data** (SIREN, electronic addresses, 3 legal payment notes). Country-specific "legal mentions" are a concrete differentiator to test in customer interviews.
- PDF drawing is ~20× slower than validation, so the product needs a job queue for big batches; cost per invoice is still negligible.

## Pending (founder actions)
- [x] Review report and approve or redirect (approved 2026-11-01)
- [ ] Re-check key competitor prices on official pages
- [ ] Landing page + waitlist (no-code)
- [ ] 30 outreach messages → 15 interviews
- [ ] Go/no-go decision at the end of the 4-week validation sprint

## Blockers
- Customer interviews and outreach must be done by the founder (Claude cannot send messages or hold calls).
- Some research sites are blocked by this environment's network policy (for example developer.altium.com); some pricing comes from secondary sources and needs re-checking.
- Cloud environment network policy blocks `deb.debian.org`, so the Factur-X generator Docker image could not be built there (verified with identical pinned libraries outside Docker). Fix: allow the host in the environment's network settings, or build locally.
- Payments from India: Stripe is invite-only → plan to use a Merchant of Record; consult a Chartered Accountant (CA) about export-of-services/GST before the first sale.

## Next actions
1. Founder: start outreach, aiming for 15 interviews in 4 weeks (validation kit). **Most important.** Use the sample PDFs as a demo in interviews.
2. Founder: run both sandboxes locally (READMEs have exact commands); report whether `docker compose build` works for the generator.
3. Me, on request: add the German XRechnung rules (needs a local machine or network allowance); XRechnung/Peppol UBL output; reverse charge and exemptions. Still no product build until the go/no-go decision.
