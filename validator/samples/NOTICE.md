# Sample files: origin and licence

| File | Origin | Licence |
|---|---|---|
| `valid/xrechnung-ubl-invoice.xml` | `src/test/business-cases/standard/01.01a-INVOICE_ubl.xml` from [itplr-kosit/xrechnung-testsuite](https://github.com/itplr-kosit/xrechnung-testsuite) tag `v2026-08-31` (commit `44c3905c`) | Apache 2.0 |
| `valid/xrechnung-cii-invoice.xml` | `src/test/business-cases/standard/01.01a-INVOICE_uncefact.xml`, same source | Apache 2.0 |
| `invalid/wrong-payable-amount-ubl.xml` | Copy of the UBL sample with `PayableAmount` changed from 336.9 to 400.00 (made by us) | Apache 2.0 (derivative) |
| `invalid/missing-issue-date-ubl.xml` | Copy of the UBL sample with `cbc:IssueDate` removed (made by us) | Apache 2.0 (derivative) |
| `invalid/not-an-invoice.xml` | Made by us | — |

These are fictional test invoices published by KoSIT for testing. They contain no real personal data.
