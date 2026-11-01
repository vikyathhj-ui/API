# Customer Validation Kit — EU E-Invoice API

Purpose: find out whether real developers will **pay** for a hosted e-invoice generation and validation API **before** we build it.
Rule: **listen more than you pitch.** In interviews, ask about the past and the present, not "would you buy this?"

---

## 1. Interview script (20–30 minutes)

**Opening (2 min)**
> "Thanks for your time. I'm researching how small software teams are handling the new EU e-invoicing rules. I'm not selling anything today. I'd like to learn how you're dealing with it."

**Context (5 min)**
1. What does your product do, and who are your customers?
2. Roughly how many invoices do your users create per month through your product?
3. Which countries are your customers in?

**The problem (10 min)**
4. Have customers asked you for XRechnung, ZUGFeRD, Factur-X or Peppol support? When was the last time?
5. What have you done about it so far? (Built it, used a library, used a vendor, ignored it?)
6. *(If they built it)* How long did it take? What was the hardest part? What still breaks?
7. *(If they use a vendor)* Which one? What do you pay? What do you dislike?
8. *(If nothing yet)* What deadline are you working against? What happens if you miss it?
9. Do you need to *send* invoices through Peppol or a French platform, or just produce correct files?
10. How do you know today whether an invoice you generate is valid?

**Value & money (5 min)**
11. If this problem disappeared tomorrow, what would that be worth to you per month?
12. Who decides on buying a tool like this, and how is it paid for (card, invoice)?
13. What would make you *not* trust an outside API with your invoice data?

**Close (3 min)**
14. "We're building a hosted API for this. Would you like to be one of three founding pilots? Free for 3 months, then a locked low price, in exchange for feedback."
15. "Who else should I talk to?"

**Write down after every call:** exact quotes, the urgency (1–5), the current solution, the price they mentioned, whether they need transmission, and the next step agreed.

---

## 2. Short survey (for forums and a waitlist form)

1. What is your role? (Founder/dev at invoicing SaaS · Plugin developer · Agency/freelancer · Accountant · Other)
2. Which e-invoice formats do your users need? (XRechnung · ZUGFeRD/Factur-X · Peppol BIS UBL · Don't know · None)
3. Which countries? (DE · FR · BE · NL · IT · PL · Other)
4. How are you solving it today? (Built in-house · Open-source library · Paid vendor · Not yet)
5. Your biggest pain with it? (free text)
6. Do you need us to *transmit* invoices (Peppol/PDP) or only *create and validate* files?
7. Monthly invoice volume through your product? (<500 · 500–5k · 5k–50k · >50k)
8. What would you pay per month for a reliable API that handles this? (<$10 · $10–30 · $30–100 · $100–300 · >$300)
9. May we contact you for a 20-minute call? (email)

---

## 3. Landing page concept (one page)

**Headline:** Valid EU e-invoices from one API call.
**Sub-headline:** Send JSON and get back Factur-X / ZUGFeRD PDFs, XRechnung or Peppol UBL, checked against the official validation rules. Built for small software teams.

**Three benefits:**
- **Ship compliance in a day, not a month:** no EN 16931 deep-dive, no Java validator to host.
- **Errors you can understand:** every validation error explained in plain English with a suggested fix.
- **Stays current:** we track XRechnung, ZUGFeRD and Peppol updates so you don't have to. EU-hosted, invoices never stored by default.

**Social proof section:** leave empty until real pilots agree to be named. **Never invent testimonials.**

**Pricing teaser:** Free tier, then plans from $19/month. Founding pilots get a locked price.

**Call to action:** "Join the early-access list" (email + survey questions 1, 2, 3, 6).

**Footer disclaimer:** Technical format generation and validation only. Not tax or legal advice.

---

## 4. Positioning statement

> For **small invoicing and billing software teams** who must support **EU e-invoicing mandates**, *[product]* is a **developer API** that **creates and validates compliant e-invoices in one call**. Unlike **€500/month compliance platforms** or **do-it-yourself open-source libraries**, we are **affordable, simple, kept up to date, and explain every error in plain language**.

---

## 5. Early-access offer

- 3 months free (up to 2,000 documents per month).
- Then **50% off for life** on any plan.
- Direct line to the founder; your feature requests get priority.
- In return: a 20-minute call every two weeks, and permission to use your company name as a reference *only if you agree later*.

---

## 6. Outreach messages

**A. GitHub issue / forum reply (only where e-invoicing is already being discussed; be helpful first)**
> "I've been digging into XRechnung/Factur-X validation recently. [Give a genuinely useful answer to their question.] Separately, I'm researching how small projects handle this. If anyone would be open to a 20-minute chat about what's been painful, I'd really appreciate it. No sales pitch."

*Do not spam issues. Only post where you add real value, and follow each project's rules.*

**B. Cold email / LinkedIn to a founder (personalize the first line every time)**
> Subject: Quick question about e-invoicing in [Product]
>
> Hi [Name],
> I saw [specific thing: their changelog / pricing page / a user asking for ZUGFeRD support].
> I'm researching how small invoicing tools are handling the German/French/Belgian e-invoice mandates, and building a lightweight API for it.
> Would you be open to a 20-minute call to tell me how you're approaching it? I'm trying to learn what actually hurts before I build anything.
> Thanks,
> [Your name]

**C. Follow-up (5–7 days later, once only)**
> "Hi [Name], just bumping this in case it got buried. Even a two-line reply on how you're handling XRechnung/Factur-X would help a lot. Thanks!"

**D. Community post (Indie Hackers / r/SaaS / Hacker News "Ask HN")**
> "Ask: How are small SaaS teams handling EU e-invoicing (XRechnung, ZUGFeRD, Factur-X, Peppol)? I'm researching the pain before building anything. Did you build it, use a library, or pay a vendor? What was hardest?"

---

## 7. Prospect list — how to build it (no invented names)

Fill in a spreadsheet with: *Company/project · URL · public contact channel · evidence of need (link) · segment · status.*

Search recipes:
1. GitHub issues: `ZUGFeRD`, `XRechnung`, `Factur-X`, `e-invoice` in invoicing/ERP repositories (sort by recent).
2. WordPress.org plugins: "invoice PDF", "WooCommerce invoice", "e-invoice". Check the support forums for e-invoice requests.
3. Product directories (Capterra, GetApp, SaaSHub): "invoicing software" filtered to Germany/France/Belgium; prefer small vendors.
4. Public threads already identified:
   - Invoice Ninja forum, *"E-invoicing without InvoiceNinja proxy integration"* (users discussing the cost of e-invoicing): https://forum.invoiceninja.com/t/e-invoicing-without-invoiceninja-proxy-integration/23415
   - Kimai blog, *"E-Invoicing 2026"*: https://www.kimai.org/en/blog/2026/e-invoicing-2026
   - "POP – Free European electronic invoicing for e-commerce" WordPress plugin (possible partner or competitor): https://fa.wordpress.org/plugins/woopop-electronic-invoice-free/

Target: 60 prospects → 30 personalized messages → 15 calls.

---

## 8. Interview log template

| Date | Person / company | Segment | Current solution | Urgency (1–5) | Needs transmission? | Price mentioned | Key quote | Next step |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
