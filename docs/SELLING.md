# Selling it: payments, launch checklist and first customers

## 1. Taking payments (no code needed for version 1)
You need a **Merchant of Record (MoR)**: a company that sells your subscription on your behalf, charges customers' cards, handles EU VAT and sales tax, and pays you out. For a solo founder in India selling to EU businesses this saves a lot of tax paperwork. Stripe accounts are invite-only in India (since May 2024, per Stripe's support pages).

Options to compare (check each one's **current** fees and whether it **accepts sellers based in India** before signing up):
- **Dodo Payments**: India-founded MoR; advertises about 4% + $0.40.
- **Paddle**: established MoR; headline about 5% + $0.50.
- **Lemon Squeezy** (owned by Stripe): headline about 5% + $0.50.

(Fee figures are from vendor and comparison pages and may have changed.)

Steps once you pick one:
1. Create three monthly subscription products: Starter $19, Growth $79, Scale $249 (or your own prices; keep `service/app/plans.py` in sync).
2. Copy each product's **checkout link** into `.env`:
   ```
   PAYMENT_LINK_STARTER=https://...
   PAYMENT_LINK_GROWTH=https://...
   PAYMENT_LINK_SCALE=https://...
   ```
3. Restart: `docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d`. The pricing buttons on your website now open checkout.
4. When a payment email arrives, run the `set-plan` / `create` command ([OPERATIONS.md](OPERATIONS.md)).

**Tax and legal (India):** ask a Chartered Accountant about invoicing export of services, GST registration and LUT (Letter of Undertaking), and how MoR payouts are treated. Do this before your first payout.

## 1b. Selling through RapidAPI (marketplace)
RapidAPI handles customer sign-up, keys, billing and quotas for its marketplace customers, and pays you via PayPal (minus its fee). The server already supports it: set `RAPIDAPI_PROXY_SECRET`. Step-by-step listing guide with copy-paste text and the OpenAPI file: [rapidapi/LISTING.md](rapidapi/LISTING.md). It still requires the API to be deployed at a public HTTPS address first.

## 2. Launch checklist
**Before telling anyone**
- [ ] Choose the final product name; check that the domain and name are free (search trademarks in the EU / your target countries)
- [ ] Deploy with HTTPS ([DEPLOY.md](DEPLOY.md)); `scripts/e2e-check.sh` passes against the live URL
- [ ] `CONTACT_EMAIL` set (a dedicated address, e.g. support@yourdomain.com)
- [ ] Terms and Privacy pages reviewed (they are **drafts**: get a lawyer's review, especially for GDPR)
- [ ] Payment provider approved and checkout links set
- [ ] Daily backups running; one restore practised
- [ ] Uptime monitor on `/v1/health`
- [ ] Try the full customer journey yourself: sign up on the site → call the API → upgrade via checkout → you run `set-plan`

**Launch week**
- [ ] Post a short "Show HN" / Indie Hackers / r/SaaS post: what it does, who it is for, the free tier, and an honest list of limitations
- [ ] Publish the free validator use-case: "Paste your ZUGFeRD/XRechnung/Factur-X file, get errors in plain English". That's the most searchable entry point
- [ ] Contact the 30 prospects from [validation/validation-kit.md](validation/validation-kit.md) with the live link

## 3. Getting the first 10 paying customers
The validation kit's interview script still applies. Use the live product as the conversation starter.

1. **Find people with the problem right now:** GitHub issues mentioning XRechnung/ZUGFeRD/Factur-X in invoicing tools; WooCommerce/WordPress invoice plugin authors; small SaaS selling to German/French/Belgian businesses.
2. **Offer a founding deal:** 3 months free, then 50% off for life, in exchange for feedback calls.
3. **Watch usage:** `python -m app.admin usage` every few days. Users with many documents are your best upgrade candidates, so email them personally.
4. **Ship what blocks a sale:** the most likely asks are XRechnung output, reverse charge / exemptions, and German national rules. Ask each prospect which one they need, then build that first.

## 4. Honest positioning (avoid over-promising)
Say clearly what works today and what doesn't (also shown on the website):
- ✅ Factur-X/ZUGFeRD EN 16931 generation (standard VAT), checked by veraPDF and Mustang with zero warnings
- ✅ EN 16931 validation of UBL/CII XML and Factur-X PDFs, with plain-English hints
- ⏳ Not yet: XRechnung/Peppol UBL output, reverse charge/exemptions, discounts/charges, German and French national rule sets
- ❌ Not offered: sending invoices over Peppol or through French certified platforms (partner with an access point for that)
- Always: "technical format generation and validation, not tax or legal advice"

## 5. Unit economics (measured, 2026-11-09)
- Generation ~0.1–0.3 s per invoice, validation ~0.06 s, on a small server. CPU cost per 1,000 documents is well under $0.01.
- Fixed costs: server about €6–10/month, domain about $1/month, backup storage about $1–3/month. **Break-even: 1 Starter customer** (after MoR fees ~$17.5 net).
- Your time is the real cost: plan for support and sales, not servers.
