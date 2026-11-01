# Phase 1 Report — Market Research & Opportunity Discovery

**Date:** 2026-11-01
**Status:** Research complete. The recommendation is still a hypothesis until real customers are interviewed (Phase 3).
**Code written so far:** none, on purpose.

---

## How to read this report

The evidence comes in four strengths, and every claim below is labelled with one of them:

| Label | Meaning |
|---|---|
| **[VERIFIED]** | Primary source: official pricing page, official docs, government rule, or the founder's own published numbers |
| **[INTEREST]** | Evidence that people want this, such as forum complaints, funding rounds or open-source projects, but no proof they would pay us |
| **[INDIRECT]** | Secondary sources: comparison blogs, aggregators, competitor-written pages. Useful but biased |
| **[HYPOTHESIS]** | My own reasoning. Must be tested |

**Research limits (stated honestly):**
- I worked through web search. Some sites (for example `developer.altium.com`) are blocked by this environment's network policy, and I could not log in to RapidAPI, G2 or Reddit to read listings and reviews directly.
- Many pricing figures come from third-party comparison pages and **disagree with each other**. Before we commit money or pricing, the important ones must be re-checked on the vendor's own page.
- I have **not** spoken to any customer. Nothing here proves that anyone will pay *us*.

---

## 1. Executive summary

**Recommendation:** build a **developer API that generates and validates EU-compliant electronic invoices** (the EN 16931 family: Factur-X / ZUGFeRD hybrid PDFs, XRechnung XML, and Peppol UBL). It is aimed at **small invoicing, billing and ERP software makers** who now have to support these formats because of legal deadlines in Belgium, France and Germany.

**Why this one:**
1. **The demand is forced by law, not created by marketing.** [VERIFIED/INDIRECT]
   - Belgium made B2B e-invoicing mandatory on 1 January 2026.
   - France requires every business to be able to receive e-invoices from September 2026, with phased issuing obligations.
   - Germany has required businesses to be able to receive e-invoices since January 2025, and issuing becomes mandatory in 2027–2028.
2. **Small software makers are caught in the middle.** The well-known API vendors are priced for mid-market companies: Invopop Pro is reported at about €500/month, and Storecove's API reportedly starts around €495/month [INDIRECT]. Open-source libraries exist, but the developer has to integrate, host and maintain them, and the formats keep changing.
3. **A beginner can build it.** The hard parts (XML schemas, validation rules, PDF/A-3 embedding) already exist as open-source building blocks. Our work is to package them, test them and keep them up to date.
4. **No AI is needed, so costs are tiny.** Each document takes milliseconds to seconds of CPU on a server that costs about €6/month. Estimated gross margin is above 85%.
5. **Customers have a reason to keep paying.** The formats are updated regularly (for example, ZUGFeRD 2.5 is rolling out), and every new customer invoice is another API call.

**What would make us drop it:** if customer interviews (Phase 3) show that small invoicing tools are content with free open-source libraries, or that they all need Peppol *transmission* (which requires certification and is not beginner-friendly) rather than *format generation*. Section 11 sets clear go/no-go criteria.

**Runner-up opportunities:**
- Template → PDF document-generation API (score 65/100). This combines naturally with the winner.
- Cron/heartbeat job monitoring (score 62.5/100).

**Honest note on your interests:** I tested the electronics and semiconductor ideas seriously because they match your background. The best of them, a *component datasheet intelligence API with an MCP server for AI hardware-design agents*, scored **59/100**. It is the most differentiated idea, but its paying demand at our scale is **unverified**. I recommend running a small, cheap validation test on it in parallel (Section 11.6) rather than building it first.

---

## 2. Market overview — the API economy in late 2026

| Signal | Evidence | Strength |
|---|---|---|
| Organizations earn money from APIs | Postman's 2025 State of the API (5,700+ respondents): about 65% of organizations generate revenue from API programs; 24% of developers design APIs with AI agents in mind; "rogue agents" making excessive calls was the top security worry (50.8%) | [INDIRECT] summaries of the [Postman report](https://www.businesswire.com/news/home/20251008162423/en) / [Nordic APIs deep dive](https://nordicapis.com/a-deep-dive-into-the-state-of-the-api-2025/) |
| The biggest API marketplace changed hands | Nokia acquired Rapid's (RapidAPI's) marketplace and tech assets in Nov 2024, to fold into its 5G network-API strategy. Rapid says the marketplace continues "as it does today" | [VERIFIED] [TechCrunch, 2024-11-13](https://techcrunch.com/2024/11/13/nokia-acquires-rapid-the-api-company-once-valued-at-1b/), [Rapid blog](https://rapidapi.com/blog/nokia-acquires-the-rapid-public-api-marketplace/) |
| Marketplace commission | RapidAPI is commonly reported at 20% of paid subscriptions; Geekflare says the split is not published | [INDIRECT] [APIScout](https://apiscout.dev/guides/best-api-marketplace-platforms-2026), [Geekflare](https://geekflare.com/guides/sell-apis/) |
| Most MCP servers earn nothing | Estimated <5% of 12,000+ MCP servers have monetized (March 2026). Apify Store is the strongest payout channel for tool builders | [INDIRECT] [godberrystudios](https://godberrystudios.com/posts/how-to-monetize-mcp-servers-2026/), [Medium](https://medium.com/mcp-server/the-rise-of-mcp-protocol-adoption-in-2026-and-emerging-monetization-models-cb03438e985c) |
| Payments made by AI agents themselves are real but still small | x402: ~165M transactions but only ~$50M cumulative volume by April 2026; analysts say much of it is protocol signaling rather than commerce | [INDIRECT] [Forkast](https://forkast.news/cloudflare-built-the-payment-layer-for-the-agentic-internet-the-agents-arent-paying-yet/), [ForkLog](https://forklog.com/en/news/bloombergs-ai-agent-transaction-volumes-overestimated-by-fifteenfold) |
| Solo API businesses can work | ScreenshotOne: founder reported 800+ paying customers and >$25k MRR on Indie Hackers; later secondary reports say ~$32k MRR and a growth plateau. Healthchecks.io: founder reported 652 paying customers / $14,043 MRR after 9 years (July 2024), and the **first paying customer came 9 months after launch** | [VERIFIED] founder posts: [Indie Hackers](https://www.indiehackers.com/post/hitting-25k-mrr-by-making-his-goals-less-ambitious-jQRZDnzwm8DFAaS4Xrq0), [Healthchecks blog](https://blog.healthchecks.io/2024/07/running-one-man-saas-9-years-in/); [INDIRECT] [Super Frameworks](https://superframeworks.com/case-study/screenshotone) |
| LLM inference is now very cheap | Claude Haiku 5.5: $0.10 / $0.50 per million input/output tokens; Sonnet 5.5: $2 / $10; Opus 5.5: $4 / $20. The Batch API gives 50% off | [VERIFIED] Anthropic pricing (cached 2026-10-06) |

**What this means for us:**
- **Cheap AI cuts both ways.** It makes AI features inexpensive to run, but it also means any developer can build "send a PDF to an LLM and get JSON back" in an afternoon. **A thin AI wrapper is not a business.** The value has to come from verified data, regulatory correctness, reliability, or maintained domain knowledge.
- **AI agents are mostly a distribution channel, not yet a paying customer.** Agents finding and calling tools through MCP is real. Agents paying for tools on their own (x402) is early. We should offer an MCP server as a free distribution feature, not as the business model.
- **Solo API businesses grow slowly.** Expect months, not weeks, before the first paying customer.

---

## 3. The 28 opportunities explored

Evidence column: **V** = verified, **I** = interest, **X** = indirect, **H** = hypothesis only, **—** = not researched in depth.

### A. AI and AI-agent APIs

| # | Idea | Main competitors & pricing found | Evidence | Verdict |
|---|---|---|---|---|
| 1 | Web page → clean Markdown / data for agents | Firecrawl: free 1,000 credits; paid ~$16–$599/mo [X] ([Firecrawl pricing](https://www.firecrawl.dev/pricing)); Jina Reader | Strong demand (X) | **Reject**: crowded, venture-funded, anti-bot arms race |
| 2 | Web search API for agents | Exa $7/1k searches ([Exa changelog](https://exa.ai/docs/changelog/pricing-update)) [V]; Tavily ~$8/1k (reported acquired by Nebius) [X]; Brave $5/1k; Perplexity $5/1k [X] | Strong demand | **Reject**: requires a search index; giants compete |
| 3 | Document parsing for RAG | LlamaParse $1.25–$12.50 per 1k pages; Reducto ~$10–40 per 1k pages [X] ([APIScout](https://apiscout.dev/guides/llamaparse-vs-reducto-best-document-ai-api-2026)) | Strong demand | **Reject**: well-funded competitors, commoditizing |
| 4 | LLM structured-output validation/repair | Built into model APIs (structured outputs) | Weak (H) | **Reject**: model providers solved it for free |
| 5 | Generic paid MCP tool server | <5% of MCP servers monetize [X] | Weak | **Reject as a business model**; keep as a distribution channel |
| 6 | Agent memory API | (not researched in depth) | — | **Reject**: venture-funded space; no founder edge |
| 7 | Invoice/receipt data extraction (OCR) | Veryfi $0.16/invoice, $500/mo starter [X] ([Veryfi pricing](https://veryfi.com/pricing)); Mindee from ~$44/mo [X]; budget tools $0.04–$0.10/doc [X] | Strong demand | **Reject**: LLMs commoditize it; prices are falling |

### B. Data APIs

| # | Idea | Competitors & pricing | Evidence | Verdict |
|---|---|---|---|---|
| 8 | SEC filings as structured JSON | sec-api.io; Apify actors $0.35–$4 per 1k records; EDGAR itself is free [X] ([sec-api](https://sec-api.io/pricing)) | Moderate | **Reject**: free source plus established player |
| 9 | Sanctions / PEP screening | OpenSanctions: commercial licence required for business use; ~€0.10/call reported by a competitor [X] ([OpenSanctions licensing](https://www.opensanctions.org/faq/commercial/paying-for-use/)) | Strong (regulated) | **Reject for now**: data licence cost plus legal liability for a beginner |
| 10 | Company / lead enrichment | Crowded (Apollo, Clearbit/HubSpot and others) | — | **Reject**: data acquisition is expensive; privacy law risk |
| 11 | Email verification | NeverBounce ~$8/1k; ZeroBounce $8–20/1k [X] ([Vendr](https://www.vendr.com/marketplace/neverbounce)) | Strong demand | **Reject**: commodity; needs IP-reputation infrastructure |
| 12 | Commodity data (FX rates, IP geolocation, holidays) | APILayer, ipinfo and others | — | **Reject**: saturated, price race to zero |
| 13 | HS-code / tariff classification & landed cost | Zonos, Avalara (custom quotes); TariffPro from $1.25/classification; GingerControl, tariffsapi.com, ustariffrates.com [X] ([comparison](https://gingercontrol.com/blog/zonos-vs-avalara-vs-gingercontrol)) | Strong (2025–26 tariffs) | **Shortlisted** (#5 below): many new entrants and legal liability |

### C. Developer APIs

| # | Idea | Competitors & pricing | Evidence | Verdict |
|---|---|---|---|---|
| 14 | HTML / template → PDF generation | DocRaptor from $15/mo for 125 docs; PDFShift from $24/mo for 2,500 credits [X] ([comparison](https://apiscout.dev/blog/best-pdf-generation-apis-2026)) | Strong, proven paying market | **Shortlisted** (#2) |
| 15 | Website screenshot API | ScreenshotOne (~$25–32k MRR solo) [V/X] | Proven | **Shortlisted, low**: crowded, browser infrastructure is costly |
| 16 | Cron / heartbeat job monitoring | Healthchecks.io ($14k MRR in 2024, solo, open source) [V]; Cronitor | Proven | **Shortlisted** (#3) |
| 17 | Webhook relay / inspection | Hookdeck, Svix (not researched in depth) | — | Reject: funded competitors |
| 18 | OpenAPI breaking-change detection | Open-source tools (oasdiff and others) | H | Reject: free tools are good enough |

### D. Semiconductor & engineering APIs

| # | Idea | Competitors & pricing | Evidence | Verdict |
|---|---|---|---|---|
| 19 | **Component datasheet intelligence** (verified specs/pinouts as JSON, with page citations; MCP server for AI design agents) | Nexar/Octopart (paid tiers, prices not published) [V]; SiliconExpert/Z2Data (sales-led) [V]; Flux datasheet import (in-house); open-source Claude skill "kicad-happy" extracts datasheets locally [I] | Interest only | **Shortlisted** (#4): differentiated, demand unverified |
| 20 | BOM lifecycle / obsolescence risk | SiliconExpert, Z2Data: quote-only, priced per active component [V] ([Z2Data pricing](https://www.z2data.com/products/pricing/)) | Strong (enterprise) | Reject: requires huge proprietary datasets |
| 21 | Multi-distributor price & stock | Nexar (free Evaluation tier up to 100 matched parts; paid tiers unpublished) [V] ([Nexar](https://nexar.com/api)); DigiKey API 1,000 req/day [V] ([DigiKey docs](https://developer.digikey.com/documentation)) | Interest: KiCad users report Octopart dropped free keys and quoted ~$25/mo for 1k queries [I] ([KiCad forum](https://forum.kicad.info/t/kicost-going-quiet/15000)) | Reject: redistributing distributor data likely violates their terms |
| 22 | BOM tariff-exposure API for electronics | Amtech BOMsense (free tool) [X]; tariff APIs above | Interest (2026 tariff stack 30–55%+) [X] ([Altium](https://resources.altium.com/p/tariff-reset-pcb-workarounds)) | **Shortlisted** (merged with #13) |
| 23 | Circuit / engineering calculator engine (C) | Free online calculators everywhere | Weak | **Reject**: no one pays for formulas |
| 24 | SPICE simulation result analysis | (none found) | Weak (H) | Reject: tiny market, no buyer found |
| 25 | KiCad/EDA design-rule & BOM checking API | Built into EDA tools; open-source plugins | H | Reject: free alternatives |

### E. Business automation APIs

| # | Idea | Competitors & pricing | Evidence | Verdict |
|---|---|---|---|---|
| 26 | **EU e-invoice generation + validation** (EN 16931) | Invopop (Dev €0, Pro ~€500/mo) [X]; Storecove (~€495/mo API, anecdotal) [I]; Apify community validator $4/1k validations, 0 users shown [X]; free web validators (easybill) | **Mandated by law** [V/X] | **WINNER** (#1) |
| 27 | Peppol access point (transmission) | Storecove, Dokapi, Invopop; registration fees from ~€1,050 [X] | Strong | Reject for now: certification, legal entity and liability. Partner instead |
| 28 | VAT-number validation | EU VIES is free | Weak | Reject: free official source; include as a small feature in #26 |

---

## 4. Competitor & gap analysis (shortlisted ideas)

### 4.1 E-invoice generation & validation (winner)

**Regulatory timeline:**
- **Belgium:** mandatory B2B e-invoicing via Peppol since 1 Jan 2026, with a grace period to 31 Mar 2026 [X] ([SPS Commerce](https://www.spscommerce.com/community/articles/e-invoicing-mandates-in-europe-the-2026-business-guide)).
- **France:** every business must be able to *receive* from Sept 2026; large and mid-size companies must *issue* from Sept 2026, and SMEs/micro from Sept 2027. Accepted formats are UBL, CII and Factur-X. *Sources conflict on details; confirm on impots.gouv.fr* [X] ([OriginStamp](https://originstamp.com/en/blog/reader/france-2026-e-invoicing-mandate-german-suppliers), [lleverage](https://www.lleverage.ai/blog/eu-e-invoicing-manufacturers-2026-guide)).
- **Germany:** receiving mandatory since Jan 2025; issuing mandatory from 2027 for turnover above €800k, and from 2028 for everyone. Formats are XRechnung and ZUGFeRD, both under EN 16931; ZUGFeRD 2.5 is rolling out [X] ([SoftCo](https://softco.com/blog/germany-e-invoicing-mandate-2026-update/)).
- **EU:** ViDA requires digital reporting for intra-EU B2B transactions from 1 July 2030 [X].

| Competitor | What they sell | Price | Their customer | Gap for us |
|---|---|---|---|---|
| Invopop | Invoicing/tax compliance API, many countries | Dev €0; Pro ~€500/mo; usage "Pops" [X] ([pricing](https://invopop.com/pricing.md)) | Funded SaaS, mid-market | €500/mo is too expensive for a 2-person invoicing tool |
| Storecove | Peppol access point + API | ~€495/mo API start (forum anecdote) [I] ([Invoice Ninja forum](https://forum.invoiceninja.com/t/e-invoicing-without-invoiceninja-proxy-integration/23415)) | Platforms needing transmission | Transmission-focused, sales-led |
| Apify community actors | Validation only (KoSIT + Mustang + veraPDF) | $4 / 1k validations [X] ([Apify](https://apify.com/kamerozkan/xrechnung-xml-batch-validator-api)) | Hobbyists | No generation, unproven, no support or SLA |
| Free web validators (easybill etc.) | Manual upload | Free | Accountants | Not an API |
| Open-source libraries (Mustangproject in Java, factur-x / drafthorse in Python, FactoorSharp in .NET) | DIY | Free | Developers with time | Developer must host, integrate, keep up with spec changes and debug cryptic validation errors |
| Doxis (ex-Klippa), Verax-Check | Validation + review platforms | Not published | Mid-market AP teams | Enterprise sales motion |

**Answers to the six questions:**
1. **Why choose us?** Send a JSON invoice and get back a valid Factur-X PDF, XRechnung XML or Peppol UBL, plus a validation report that explains errors in plain English with suggested fixes. Developer-tier pricing from about $19/month, EU-hosted, with no documents stored by default.
2. **Why not Invopop or Storecove?** Price (about 25× cheaper at small volume) and simplicity. Many small tools only need *correct files*; their customers handle transmission another way. In Germany, B2B delivery by email is allowed.
3. **Why not build it themselves?** It is possible, but it costs several developer-weeks. They would need to learn EN 16931, wire up a Java validator from a Python or PHP stack, master PDF/A-3 embedding, and then keep tracking spec updates (XRechnung 3.x, ZUGFeRD 2.5). Our price is less than one hour of developer time per month. [HYPOTHESIS: must be confirmed in interviews]
4. **What makes us hard to replace?** Once integrated, switching means re-testing invoice output, and nobody touches invoicing code that works. Over time we add a growing library of real-world edge-case fixtures, error explanations and country coverage (Belgium, France, Germany, then Poland KSeF, Romania and others).
5. **What justifies paying every month?** Every invoice their users issue is a call. Formats change. Compliance is a recurring obligation.
6. **How do we build an advantage?** Narrow focus and the best documentation. A plain-language error explainer. Fixtures and test suites developers can run. Fast response to spec updates. A free MCP server and a free validator page to drive SEO traffic.

**Main weaknesses (honest):**
- Big vendors could add a cheap tier.
- Open-source libraries are good enough for skilled teams.
- Transmission (Peppol / French PDP platforms) is where much of the compliance value sits, and we do not do it at first.

### 4.2 Template → PDF generation (runner-up)
Proven paying market: DocRaptor and PDFShift [X]; ScreenshotOne shows that a solo founder can build a rendering API business [V]. The weakness is zero differentiation: there are dozens of competitors, plus Gotenberg (open-source, self-hostable). **Best used as a feature of the winner** ("generate the visual invoice PDF *and* embed the compliant XML"), not as a standalone business.

### 4.3 Cron / heartbeat monitoring
Proven by Healthchecks.io (solo, $14k MRR in 2024, 9 months to the first paying customer) [V]. The weaknesses are a crowded market, a strong open-source incumbent (which can be self-hosted), and slow growth. Low risk, low upside, no edge for you.

### 4.4 Component datasheet intelligence (your-background option)
**Gap:**
- Octopart moved away from free API keys, and hobby/small-tool developers complain about cost [I].
- SiliconExpert and Z2Data are sales-led enterprise products [V].
- AI PCB-design startups are being funded: Circuit Mind ~$25M (2026), Flux reportedly ~$27M (2026), CopperPilot $390k pre-seed [X] ([Dealroom](https://dealroom.co/news/164658-circuit-mind-raises-18-5m-series-a-to-automate-circuit-board-design/), [Semiengineering](https://semiengineering.com/startup-funding-q2-2026/)). Their agents need structured component facts.

**But:**
- Those funded startups build their own pipelines (Flux has datasheet import in-house [V]).
- Hobbyists already use free open-source Claude skills that do this locally [I].
- Extraction costs well under $0.01 per datasheet with Haiku-class models, so the "service" alone is easy to copy.

**The only defensible version is a *verified, page-cited, versioned dataset* that grows over time.** Building that takes a long time and has no proven buyer at our price.

**Data-licensing risk:** the facts in a datasheet are generally not copyrightable, but redistributing the PDFs themselves, or scraping distributor sites, may breach copyright or terms of service. This needs care.

### 4.5 Tariff / HS exposure for electronics BOMs
There is real 2026 pain: a stacked tariff of roughly 30–55%+ on China-origin electronics, and a separate HTS lookup for every line item [X]. But 2025–26 brought a rush of new entrants (tariffsapi, ustariffrates, TariffLens, GingerControl, TariffPro), a free tool (BOMsense), and **legal liability for wrong classifications**. Rates also change by executive action, so the data needs constant maintenance. Too risky for a beginner.

---

## 5. Pricing analysis (what the market charges)

| Category | Low end | Typical | High end |
|---|---|---|---|
| Email verification | $3/1k (bulk) | $8/1k | $20/1k |
| Web search for agents | $1/1k (Perplexity fast) | $5–8/1k | $15/1k (Exa deep reasoning) |
| Document parsing | $1.25/1k pages | $10/1k pages | $40/1k pages |
| Invoice extraction | $0.04/doc | $0.10/doc | $0.16/doc (Veryfi) |
| HTML→PDF | ~$0.01/doc (PDFShift volume) | $0.12/doc (DocRaptor entry) | — |
| E-invoice validation only | $4/1k (Apify) | — | — |
| E-invoice compliance platform | €0 dev tier | ~€500/mo (Invopop Pro, Storecove) | Enterprise custom |
| Component data (Octopart) | Free evaluation (100 matched parts) | ~$25/mo for 1k queries (user report) | Enterprise custom |

**The pattern:** developer APIs usually sell as monthly subscriptions with included volume plus overage. Pure pay-per-call works for agents and occasional users. The e-invoice market has a **price gap between €0 (do-it-yourself / validation-only) and ~€500/month (platforms)**. That gap is our target.

---

## 6. Weighted scoring

Each criterion is scored 1–10. The weighted score is Σ(weight × score / 10), giving a total out of 100.

| Criterion (weight) | E-invoice gen+validate | Template→PDF | Cron monitoring | Tariff/HS electronics | Component datasheet intel | Sanctions screening | Invoice OCR | Screenshot API | SEC data | Email verification | Agent web extraction | C calculator engine |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Verified demand (20) | 8 | 8 | 7 | 6 | 4 | 7 | 8 | 8 | 6 | 9 | 9 | 2 |
| Willingness to pay (15) | 7 | 6 | 5 | 7 | 5 | 8 | 6 | 6 | 6 | 7 | 7 | 2 |
| Differentiation (15) | 5 | 3 | 2 | 4 | 7 | 3 | 2 | 2 | 2 | 1 | 1 | 5 |
| Profit margin (15) | 9 | 8 | 9 | 8 | 8 | 6 | 7 | 6 | 8 | 6 | 4 | 9 |
| Dev feasibility (10) | 5 | 7 | 7 | 4 | 5 | 4 | 6 | 6 | 5 | 4 | 4 | 8 |
| Recurring revenue (10) | 9 | 8 | 9 | 6 | 7 | 9 | 7 | 8 | 8 | 6 | 7 | 3 |
| Acquisition feasibility (10) | 6 | 5 | 4 | 5 | 5 | 3 | 3 | 4 | 4 | 3 | 3 | 4 |
| Infra affordability (5) | 9 | 7 | 9 | 8 | 8 | 7 | 7 | 6 | 6 | 5 | 4 | 10 |
| **TOTAL /100** | **72.0** | **65.0** | **62.5** | **59.5** | **59.0** | **59.0** | **58.0** | **58.0** | **56.0** | **54.5** | **52.0** | **48.0** |

**Why each score for the winner:**
- **Demand 8:** legal mandates are verified, and three countries have live or near deadlines. Not 10, because we have not yet heard from customers ourselves.
- **Willingness to pay 7:** competitors charge about €500/mo, and businesses pay for compliance. The open question is how much *small* tools will pay.
- **Differentiation 5:** price gap plus developer experience. Technically copyable, so only medium.
- **Margin 9:** no AI cost, CPU-light (Section 8).
- **Feasibility 5:** open-source building blocks exist, but EN 16931 is detailed and a beginner needs to learn XML/PDF concepts. It is the hardest part of this plan.
- **Recurring 9:** usage happens with every invoice; compliance is ongoing.
- **Acquisition 6:** reachable through developer SEO ("ZUGFeRD API Python", "XRechnung validator API"), open-source invoicing communities, plugin ecosystems and a free validator tool.
- **Infrastructure 9:** a single small EU server is enough at the start.

**Sensitivity check:** if I lower the winner's demand to 6 and its feasibility to 4, it still scores 67, above the runner-up. If I raise the component idea's demand to 7 (if interviews prove demand), it reaches 65. That is why it gets a parallel validation test.

### Top three
1. **EU e-invoice generation + validation API: 72.0**
2. **Template → PDF document generation API: 65.0** (fold into #1 as a feature)
3. **Cron/heartbeat monitoring: 62.5** (fallback)

---

## 7. The recommended business — in detail

**What we build** (working name *"InvoiceFormat API"*; trademark check needed):
A REST API plus a free MCP server.
- `POST /v1/invoices/generate`: send invoice data as simple JSON and choose `factur-x`, `zugferd`, `xrechnung-cii`, `xrechnung-ubl` or `peppol-bis-ubl`. You get back the file (XML, or a PDF/A-3 with embedded XML).
- `POST /v1/invoices/validate`: upload XML or PDF and get a structured report (errors, warnings, rule IDs, and plain-language explanations with suggested fixes).
- `POST /v1/invoices/convert`: convert between formats (for example CII ↔ UBL).
- Later: extract data from incoming e-invoices, verify VAT numbers, and partner with a Peppol access point for transmission.

**The problem it solves:** small invoicing, billing and ERP software must produce legally valid e-invoices for German, French and Belgian customers. Doing it in-house means learning a large standard and maintaining it forever.

**Who pays:**
1. Small invoicing/billing SaaS companies (1–20 employees) selling into DE/FR/BE.
2. Developers of plugins for WooCommerce, Shopify, Odoo, WordPress and similar platforms.
3. Agencies and freelancers who build custom ERP or e-commerce systems for EU SMBs.
4. Vertical SaaS that invoices on behalf of users (field services, freelance marketplaces, coworking, time tracking).
5. Accounting-automation tools and AI agents (through MCP).

**Why they pay:** a legal deadline, the risk of rejected invoices (customers do not pay invalid invoices), and the cost of developer time.

**Alternatives:** do it yourself with open source; Invopop or Storecove; ignore it until forced.

**How hard is it to build:** medium. The MVP (generate + validate for Factur-X/ZUGFeRD and XRechnung) takes roughly **6–10 weeks** of part-time work for a beginner working with Claude Code [HYPOTHESIS].

**Development costs (one-time):** about $0–30 (domain ~$12/yr; everything else free/open-source).

**Operating costs (monthly, estimates):** €6–15 for a server, $0–5 for backups, $0 for monitoring (free tiers), and payment fees per sale. **Total fixed ≈ $15–40/month.**

**Pricing hypothesis (validate before launch):**

| Plan | Price | Included | Overage |
|---|---|---|---|
| Free | $0 | 50 documents/mo, watermark-free, validation unlimited at low rate | — |
| Starter | $19/mo | 500 documents | $0.03/doc |
| Growth | $79/mo | 5,000 documents | $0.015/doc |
| Scale | $249/mo | 30,000 documents | $0.008/doc |
| Enterprise / self-host licence | custom | SLA, on-premise Docker image | — |

**Main commercial risks:** see Section 10.

**Recurring revenue potential:** high per customer (invoices recur monthly). The market is bounded but large: there are many thousands of invoicing tools in Europe [HYPOTHESIS: not quantified, and I will not invent a market-size number].

---

## 8. Financial assumptions & unit economics

**All figures are ESTIMATES. There is no actual revenue yet.**

### 8.1 Cost per request
| Cost item | Assumption | Cost per 1,000 docs |
|---|---|---|
| Compute | Original assumption: 0.2–1.0 s CPU per doc. **Measured 2026-11-01 for validation only** (see `sandbox/validator/README.md`): median 10 ms, ~87 docs/s on 1 CPU. PDF generation is not measured yet. A €5.99/mo 2-vCPU ARM server ([Hetzner, after the 2026 price rises](https://capitalandcompute.net/blog/hetzner-price-increase-2026/)) is far more than enough at launch | < $0.01 (validation, measured); generation TBD |
| AI inference | None in the core product. Optional plain-English error explanations can be pre-written templates (no LLM). If an LLM is used: Haiku 5.5 at ~2k input + 300 output tokens ≈ $0.00035/call | $0 (or ~$0.35) |
| Database | Postgres on the same server (usage counters, keys) | ~$0 |
| Storage | Documents processed in memory and not stored by default (also helps GDPR) | ~$0 |
| Bandwidth | ~100 KB per PDF; Hetzner includes TBs of traffic | ~$0 |
| Marketplace commission | Only if sold via RapidAPI/Apify (~20%) | 20% of revenue |
| Payment processing | Merchant of Record (Paddle / Lemon Squeezy: 5% + $0.50; Dodo: ~4% + $0.40) [X] | per transaction |

**Revenue per 1,000 docs:** Starter ≈ $38 (=$19/500), Growth ≈ $15.80, Scale ≈ $8.30.

### 8.2 Margin per plan (monthly)
| Plan | Revenue | Payment fee (5% + $0.50) | Compute (at full usage) | Gross profit | Gross margin |
|---|---|---|---|---|---|
| Starter $19 | $19.00 | $1.45 | ~$0.03 | $17.52 | **92%** |
| Growth $79 | $79.00 | $4.45 | ~$0.25 | $74.30 | **94%** |
| Scale $249 | $249.00 | $12.95 | ~$1.50 | $234.55 | **94%** |

Formulas used: Gross profit = Revenue − Direct costs; Gross margin = Gross profit / Revenue × 100.

### 8.3 Break-even
Fixed costs ≈ $40/month (a generous estimate). Contribution margin ratio ≈ 0.92.
Break-even revenue = $40 / 0.92 ≈ **$44/month**, which is **3 Starter customers or 1 Growth customer.**
The real cost is **your time**, which this formula does not capture.

### 8.4 Three scenarios (12 months after launch, ESTIMATES)
| Scenario | Paying customers | Avg revenue / customer | MRR | Annualized | Basis |
|---|---|---|---|---|---|
| Conservative | 5 | $25 | $125 | $1.5k | Healthchecks took 9 months to the first $5 customer |
| Base | 25 | $45 | $1,125 | $13.5k | Mix of Starter/Growth, a few agencies |
| Optimistic | 80 | $70 | $5,600 | $67k | Strong SEO, 2–3 plugin/platform partnerships |

**Customer acquisition cost (CAC):** target near $0 cash (content, open source, direct outreach), paid with your time. **Lifetime value (LTV):** not calculable until we have real churn data. Do not trust any LTV number before about 6 months of real customers.

### 8.5 Abuse & cost safeguards (designed in from day one)
- API-key rate limits and hard monthly caps on the free tier.
- Maximum file size (for example 10 MB) and processing timeouts.
- No AI calls in the hot path; any LLM feature gets a per-key budget cap.
- Prepaid or card-on-file before overage is allowed.

---

## 9. Technical feasibility (beginner-friendly)

**What the system is, in plain words:** a small web server. A customer's program sends it invoice data over the internet (an "API call"). The server turns the data into the right file format, checks it against the official rules, and sends the result back. A database remembers who our customers are and how many calls they have made.

**Technology choices:**

| Part | Technology | Why |
|---|---|---|
| API server | **Python + FastAPI** | Beginner-friendly, generates documentation automatically, huge ecosystem |
| E-invoice generation | Python libraries (`factur-x`, `drafthorse`) and/or **Mustangproject** (Java, Apache 2.0) | Proven open-source implementations of the standards |
| Official validation | **KoSIT Validator** (Java) with XRechnung configuration; veraPDF for PDF/A | These are the reference validators the German authorities use |
| Database | PostgreSQL | Reliable and free |
| Rate limiting / caching | Redis (optional at first) | Can start with Postgres-only and add Redis when needed |
| Packaging | **Docker + Docker Compose** | Runs Python and Java side by side reproducibly |
| Hosting | One EU VPS (Hetzner Germany/Finland) | Cheap, and EU data residency is a selling point |
| Payments | Merchant of Record (Paddle / Lemon Squeezy / Dodo Payments) | Stripe is invite-only in India since May 2024 [V] ([Stripe support](https://support.stripe.com/questions/stripe-accounts-are-invite-only-in-india)); an MoR also handles EU VAT for us |

**Where C fits:** honestly, **nowhere in this product's MVP.** The work is XML, PDF and business rules, and mature libraries in Python and Java handle it. Writing it in C would be slower to build, more bug-prone, and no faster where it matters (the bottleneck is the validator, not our code). I will not force C into the project. If you want C practice later, a good spot is a small, fast pre-check of invoice arithmetic (line totals, VAT sums with exact decimal math) called from Python, but only if benchmarks show a need.

**Hardest parts for a beginner:** understanding EN 16931 fields; PDF/A-3 compliance; running a Java validator inside our Docker setup; writing good tests. Claude Code can help with all of these, step by step.

---

## 10. Risk analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Small tools are happy with free open-source libraries | Medium | High | **Test in interviews before building.** Offer what libraries don't: hosting, plain-English errors, spec updates, support |
| Customers need *transmission* (Peppol / French PDP), not files | Medium | High | Ask in interviews. Plan a partnership/referral with a Peppol access point instead of becoming one |
| A big vendor launches a cheap developer tier | Medium | Medium | Win on developer experience, docs, speed of updates, niche focus |
| Wrong output causes rejected invoices / liability | Medium | High | Always validate with the official validator before returning; clear terms of service; limitation of liability; no tax advice |
| Spec changes (XRechnung, ZUGFeRD 2.5, Peppol BIS updates) | High (certain) | Medium | This is also our reason to exist. Track release notes; automated regression tests |
| Privacy (invoices contain personal and company data) under GDPR | Certain | High | Process in memory, no storage by default, EU hosting, a data processing agreement (DPA) template, delete logs of payloads |
| Payments/payouts from India | Medium | Medium | Use a Merchant of Record; consult an Indian CA about export-of-services invoicing and GST/LUT |
| Founder skill gap / slow build | High | Medium | Build in small, tested steps; Claude Code assists; narrow MVP scope |
| Marketplace dependence | Low | Low | Marketplaces are a secondary channel only |
| Open-source licence compliance | Low | Medium | Use Apache/BSD/MIT components; record licences; avoid AGPL in the hosted service unless we comply |
| Slow growth (months to the first customer) | High | Medium | Keep costs near zero; set go/no-go checkpoints |

**Regulatory note:** this is tax-related software. We provide *format generation and technical validation*, not tax or legal advice. Confirm the French PDP rules (only accredited platforms may *transmit* in France) before marketing anything there.

---

## 11. Customer validation plan (Phase 3 — before any code)

**Important:** I cannot send emails, post on forums, or hold interviews. **You must do the outreach.** I have prepared everything you need in [`validation/validation-kit.md`](validation/validation-kit.md).

### 11.1 Ideal customer profiles (ICP)
1. **"Indie invoicing SaaS":** 1–10 people; sells invoicing, billing, time-tracking or field-service software; has customers in DE/FR/BE; a developer-founder writes the code.
2. **"Plugin developer":** maintains a WooCommerce/Shopify/Odoo/WordPress invoicing or PDF-invoice plugin with EU users.
3. **"Agency":** builds custom shops or ERPs for German/French SMBs.

### 11.2 Where to find them (public channels only)
- GitHub: open-source invoicing projects and their issue trackers where users ask for XRechnung/ZUGFeRD/Factur-X support (search `ZUGFeRD`, `XRechnung`, `Factur-X` in issues).
- Public discussions already found: [Invoice Ninja forum thread on e-invoicing costs](https://forum.invoiceninja.com/t/e-invoicing-without-invoiceninja-proxy-integration/23415), [Kimai blog on e-invoicing 2026](https://www.kimai.org/en/blog/2026/e-invoicing-2026), the WordPress plugin directory (for example the "POP" e-invoicing plugin), which shows plugin authors are working on this.
- WordPress.org / WooCommerce marketplace plugin listings for "invoice PDF" (contact via their public support pages).
- Indie Hackers, Hacker News ("Ask HN"), r/SaaS, r/de_EDV and German/French developer communities.
- LinkedIn: founders of small invoicing tools in DE/FR/BE.

### 11.3 First segments to approach (in order)
1. Maintainers of open-source invoicing tools with open GitHub issues about e-invoicing (warm, public, technical).
2. WooCommerce/WordPress invoice-PDF plugin authors.
3. Small B2B SaaS companies in Germany and France with invoicing features.

### 11.4 Strategy for the first three customers
1. Publish a **free web validator page** and a **free MCP validation tool** (low effort, builds trust and SEO).
2. Do 15+ problem interviews (script in the kit). Do not pitch; learn.
3. Offer a **founding-customer pilot**: 3 months free, then $19–79/mo locked for life, in exchange for weekly feedback and a testimonial.
4. Build for those three pilots first and ship features they actually ask for.

### 11.5 Go / no-go criteria (end of a 4-week validation sprint)
| Metric | GO if ≥ | NO-GO / pivot if |
|---|---|---|
| Problem interviews completed | 15 | — |
| Interviewees with an active need and a deadline ≤ 12 months | 6 | < 3 |
| Say they would pay ≥ $19/mo (specific, not "maybe") | 5 | < 2 |
| Signed pilot / letter of intent / pre-payment | 3 | 0 |
| Waitlist signups from targeted posts | 30 | < 10 |
| Main need is files (not transmission) | majority | majority need Peppol/PDP transmission → reconsider partner-only model or pivot to #2/#3 |

### 11.6 Parallel low-cost test for the electronics idea
Spend **≤ 3 hours a week** on it:
- Post a short demo concept, "verified, page-cited datasheet specs as JSON + MCP for hardware AI agents," in KiCad / EEVblog / r/PrintedCircuitBoard and AI-hardware founder communities.
- Contact five AI-hardware startups through their public contact channels.
- **GO criterion:** at least 2 startups say they would pay ≥ $200/month for a data feed. Otherwise drop it.

---

## 12. Immediate next steps

| # | Action | Who | Time |
|---|---|---|---|
| 1 | Read this report; challenge anything that seems wrong | You | 1 h |
| 2 | Decide: approve the e-invoice direction for validation, or pick another shortlisted idea | You | — |
| 3 | Re-check key competitor prices on official pages (Invopop, Storecove, Apify validator) | You + me | 1 h |
| 4 | Set up a one-page landing page plus a waitlist form (no code needed: Carrd/Tally free tiers) using the copy in the validation kit | You (I can help) | 2 h |
| 5 | Send 30 personalized outreach messages using the templates; aim for 15 calls | You | 2 weeks |
| 6 | Record interview notes in the template; I'll synthesize them | You → me | ongoing |
| 7 | Go/no-go decision at the end of week 4 | Both | 1 h |
| 8 | Only after GO: Phase 4 architecture and Phase 5 Docker MVP | Me + you | — |

Meanwhile (no business risk, good for learning), I can set up a **Docker learning sandbox** that runs the open-source KoSIT validator and validates a sample XRechnung. That would teach you Docker and test our core technical assumption without building the product. **I will only do this if you approve it.**

---

## Glossary
- **API:** a way for one program to ask another program to do something over the internet.
- **MRR:** monthly recurring revenue, the total of all monthly subscriptions.
- **Gross margin:** the percentage of revenue left after the direct cost of serving customers.
- **EN 16931:** the European standard that defines what an electronic invoice must contain.
- **Factur-X / ZUGFeRD:** a normal-looking PDF invoice with a machine-readable XML file embedded inside it (the same standard under French and German names).
- **XRechnung:** the German e-invoice format, pure XML.
- **Peppol:** a network for sending e-invoices between businesses, like email for invoices; requires certified "access points".
- **Merchant of Record (MoR):** a company that sells your product on your behalf and handles global sales tax and payments for a fee.
- **MCP:** Model Context Protocol, a standard way for AI assistants and agents to discover and use tools such as our API.
