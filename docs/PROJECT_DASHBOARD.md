# Project Dashboard

_Last updated: 2026-11-01_

| Item | Status |
|---|---|
| **Current phase** | Phase 1 complete → waiting on founder decision to start **Phase 3: Customer validation** (Phase 2 scoring done inside the Phase 1 report) |
| **Current product decision** | Candidate: EU e-invoice generation + validation API (score 72/100). Fallbacks: template→PDF API (65), cron monitoring (62.5). Parallel low-cost test: component datasheet intelligence (59) |
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
| 3 | Customer validation | ⏳ Next — kit ready in [validation/validation-kit.md](validation/validation-kit.md) |
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

## Pending (founder actions)
- [ ] Review report and approve or redirect
- [ ] Re-check key competitor prices on official pages
- [ ] Landing page + waitlist (no-code)
- [ ] 30 outreach messages → 15 interviews
- [ ] Go/no-go decision at the end of the 4-week validation sprint

## Blockers
- Customer interviews and outreach must be done by the founder (Claude cannot send messages or hold calls).
- Some research sites are blocked by this environment's network policy (for example developer.altium.com); some pricing comes from secondary sources and needs re-checking.
- Payments from India: Stripe is invite-only → plan to use a Merchant of Record; consult a Chartered Accountant (CA) about export-of-services/GST before the first sale.

## Next actions
1. Founder decision on direction.
2. (Optional, needs approval) Docker learning sandbox: run the open-source KoSIT validator on a sample XRechnung to test the core technical assumption.
