# Selling on RapidAPI: step by step

RapidAPI is a marketplace. Customers subscribe and pay **RapidAPI**. RapidAPI forwards each call to **your server** and pays you (minus its marketplace fee) via **PayPal**, the only payout method in RapidAPI's provider docs. RapidAPI handles customer accounts, API keys, quotas and billing for marketplace customers.

```
customer ──(their RapidAPI key)──▶ RapidAPI gateway ──(adds X-RapidAPI-Proxy-Secret,
                                                       X-RapidAPI-User, X-RapidAPI-Subscription)──▶ your server
```

## Before you start: two things RapidAPI needs from you
1. **Your API deployed at a public HTTPS address**, e.g. `https://api.yourdomain.com` ([../DEPLOY.md](../DEPLOY.md)). RapidAPI cannot reach a computer or cloud dev session. Use the exact `https://` address as the base URL. Community reports say an http→https redirect can drop RapidAPI's secret header.
2. **A PayPal account** (a business account is recommended; check that it can receive international payments in India).

UI labels below come from RapidAPI's documentation and may differ slightly in the current dashboard.

## Step 1: Create the API project
1. On rapidapi.com, open **My APIs** (Studio) → **Add API Project**.
2. **Name:** `EU E-Invoice API (Factur-X, ZUGFeRD)`
3. **Short description:** see below.
4. **Category:** choose the closest business/finance category offered (e.g. *Business Software*, *Business* or *Financial*).
5. **Team/owner:** your personal account.
6. **Specify using:** choose to upload an OpenAPI file, and upload [`openapi.json`](openapi.json) from this folder (OpenAPI 3.0.3, validated).
   *(If the import page refuses the file, create the two endpoints by hand: `POST /v1/invoices` and `POST /v1/validate`.)*

## Step 2: Base URL and security
1. In the project, set the **Base URL** to your deployed address, e.g. `https://api.yourdomain.com` (no trailing slash).
2. Find the **X-RapidAPI-Proxy-Secret** value (in the project's gateway/security settings). Copy it.
3. On your server, put it into `.env`:
   ```
   RAPIDAPI_PROXY_SECRET=<paste the value>
   ```
   then restart the API:
   ```bash
   docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d api
   ```
   From now on, calls carrying the correct secret are accepted as RapidAPI customers. A wrong secret gets `403 invalid_proxy_secret`. Your direct customers (own website, own keys) keep working unchanged.

## Step 3: Pricing plans (Monetize)
RapidAPI uses up to four public tiers. Suggested to mirror the website prices (one request = one call):

| RapidAPI tier | Price / month | Included requests | Hard limit? | Overage per extra request | Rate limit |
|---|---|---|---|---|---|
| BASIC | $0 | 50 | yes (no overage) | n/a | 10 / minute |
| PRO | $19 | 500 | no | $0.04 | 60 / minute |
| ULTRA | $79 | 5,000 | no | $0.02 | 120 / minute |
| MEGA | $249 | 30,000 | no | $0.01 | 300 / minute |

Notes:
- RapidAPI's marketplace fee is not published in the docs I could check. A third-party source says about 20%, plus PayPal fees. If that's right, PRO pays you roughly $15. You may price RapidAPI plans a little higher than your website to compensate.
- On RapidAPI, **every request counts**, including ones rejected for bad input. On your own website, invalid input is free. Say so in the plan description.
- RapidAPI enforces these quotas; your server keeps a generous safety limit (300/minute per RapidAPI user) and logs usage per RapidAPI username.

## Step 4: Listing content (copy and paste)

**Short description**
> Create and validate EU e-invoices: JSON → Factur-X/ZUGFeRD PDF (EN 16931, PDF/A-3). Validate UBL/CII/PDF with plain-English errors.

**Long description**
```markdown
## EU e-invoicing in one API call

Belgium, France and Germany now require structured e-invoices. This API lets your software
produce and check them without learning EN 16931.

### Generate: `POST /v1/invoices`
Send seller, buyer, lines and VAT rates as JSON. **No totals needed**: line totals, VAT per rate
and the amount due are calculated for you, so arithmetic rules can't fail.
You get a **Factur-X / ZUGFeRD PDF** (PDF/A-3b with embedded EN 16931 XML), or the XML only,
or a JSON object with totals + XML + PDF.

Every output is checked in our test suite with the independent validators **veraPDF** (PDF/A)
and **Mustang** (Factur-X, including the French 2026 rules): zero errors, zero warnings.

### Validate: `POST /v1/validate`
Upload UBL or CII XML, or a Factur-X / ZUGFeRD PDF. Get `valid: true/false` plus every error and
warning with its rule ID, location and a **plain-English hint** for common rules
(e.g. BR-CO-16 "amount due must equal total with VAT − paid + rounding").
Engine: official KoSIT Validator with the CEN EN 16931 rules.

### Supported today
- Factur-X / ZUGFeRD EN 16931 profile, invoices and credit notes
- Multiple standard VAT rates, bank transfer details
- French legal mentions (PMD/PMT/AAB notes), SIREN, electronic addresses
- Validation of UBL 2.1 and CII D16B, as XML or inside PDF

### Not yet
XRechnung and Peppol UBL output, reverse charge / VAT exemptions, document-level discounts,
German (BR-DE) and French (BR-FR) national validation rules.

### Privacy
Invoice contents are processed in memory and never stored.

*Technical format generation and validation only; not tax or legal advice.*
```

**Tags:** `e-invoice`, `einvoice`, `factur-x`, `zugferd`, `xrechnung`, `en16931`, `invoice`, `pdf`, `pdf-a`, `vat`, `peppol`, `validation`, `ubl`, `cii`

**Website / Terms links:** your deployed `https://api.yourdomain.com`, `/terms`, `/privacy`.

## Step 5: Test inside RapidAPI, then publish
1. Open your API's page in RapidAPI's test console. Subscribe yourself to **BASIC**.
2. Test **POST /v1/invoices** with the pre-filled example body. You should get a PDF (or use `format=json`).
3. Test **POST /v1/validate** with a small XML file.
4. On your server, check that the call arrived as a RapidAPI customer:
   ```bash
   docker compose exec api python -m app.admin usage
   ```
   You should see a line `rapidapi:<your RapidAPI username>`.
5. Set the API's visibility to **Public**.
6. In your account's payout/payment settings, connect **PayPal**.

## After launch
- Answer questions in the API's RapidAPI discussion tab quickly. Responsiveness shows on the listing.
- Watch usage weekly (`app.admin usage`): RapidAPI customers appear as `rapidapi:<username>`.
- Keep your own website too: RapidAPI brings discovery, while direct customers avoid the marketplace fee.

## Sources
- RapidAPI docs: [Additional Request Headers](https://docs.rapidapi.com/docs/additional-request-headers) (headers added by the proxy), [Adding APIs](https://docs.rapidapi.com/docs/add-api-getting-started), [OpenAPI documents](https://docs.rapidapi.com/docs/adding-and-updating-openapi-documents), [Payouts and Finance](https://docs.rapidapi.com/docs/payouts-and-finance) (PayPal only)
- Header verification pattern and the redirect pitfall: community threads ([FastAPI middleware](https://dev.to/mandarvaze/how-to-write-middleware-using-fastapi-2gl), [Heroku header issue](https://community.latenode.com/t/heroku-fails-to-pass-along-the-x-rapidapi-proxy-secret-header/27127))
- Fee estimate (~20%): third-party, unverified ([comparison blog](https://x402-marketplace-nine.vercel.app/blog/payapi-market-vs-rapidapi))
