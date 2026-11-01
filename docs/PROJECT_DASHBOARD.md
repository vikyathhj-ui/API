# Project Dashboard

_Last updated: 2026-11-01_

| Item | Status |
|---|---|
| **Current phase** | **Phase 3: Customer validation** (founder approved direction 2026-11-01). Technical feasibility spike done in parallel |
| **Current product decision** | **Approved for validation:** EU e-invoice generation + validation API (score 72/100). Fallbacks: template→PDF API (65), cron monitoring (62.5). Parallel low-cost test: component datasheet intelligence (59) |
| **Technical feasibility** | ✅ Official KoSIT validator + EN 16931 rules running in Docker; 66/66 official test invoices pass; median 10 ms/validation. See [sandbox/validator/README.md](../sandbox/validator/README.md) |
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

## Learned from the sandbox (affects Phase 4 design)
- Each country variant (XRechnung standard/extension/CVD, Peppol, Factur-X) needs its own rule profile and severity overrides; generic EN 16931 is too strict for some German variants.
- German BR-DE rules must still be added (official host blocked in the cloud environment; should work on a local machine).
- The validator has no authentication and no size limit, so our API layer must add keys, rate limits and a max upload size.

## Pending (founder actions)
- [x] Review report and approve or redirect (approved 2026-11-01)
- [ ] Re-check key competitor prices on official pages
- [ ] Landing page + waitlist (no-code)
- [ ] 30 outreach messages → 15 interviews
- [ ] Go/no-go decision at the end of the 4-week validation sprint

## Blockers
- Customer interviews and outreach must be done by the founder (Claude cannot send messages or hold calls).
- Some research sites are blocked by this environment's network policy (for example developer.altium.com); some pricing comes from secondary sources and needs re-checking.
- Payments from India: Stripe is invite-only → plan to use a Merchant of Record; consult a Chartered Accountant (CA) about export-of-services/GST before the first sale.

## Next actions
1. Founder: run the sandbox locally (README has exact commands) to learn Docker basics.
2. Founder: start outreach, aiming for 15 interviews in 4 weeks (validation kit).
3. Me, on request: add German XRechnung rules locally; spike on Factur-X/ZUGFeRD PDF generation (the biggest remaining technical unknown). Still no product build until the go/no-go decision.
