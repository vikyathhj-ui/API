> **Note (2026-11-09):** this validator is now part of the product stack. It is started by the root `docker-compose.yml` as an internal service. This folder can still be run on its own for experiments (commands below).

# Sandbox: E-Invoice Validator in Docker

**What this is:** a learning sandbox, *not* the product. It runs the official open-source **KoSIT Validator** (the reference e-invoice checker used by German authorities) inside Docker, with the **European EN 16931 rules**, and tests it automatically.

**Why we built it first:** to prove our riskiest technical assumption cheaply. *Can we run official validation rules ourselves, reliably and fast?* **Answer: yes.** See the measured results below.

---

## The big picture (plain language)

```
 your computer                                Docker container (isolated box)
┌─────────────────────┐   HTTP POST invoice   ┌──────────────────────────────────────┐
│ run-tests.sh / curl │ ────────────────────▶ │ KoSIT Validator (Java)               │
│                     │                       │  1. Which kind of invoice is this?   │
│                     │ ◀──────────────────── │  2. Structure check (XML Schema)     │
└─────────────────────┘  200 = OK             │  3. Business rules (EN 16931)        │
                         406 = invalid        │  4. Writes a report (XML)            │
                         + report             └──────────────────────────────────────┘
```

- **Docker image** = a frozen package with Java + the validator + the rules. Same on every computer.
- **Container** = a running copy of that image.
- **XML Schema check** = "Are the right fields there, in the right order?" (like a form with required boxes)
- **Schematron business rules** = "Does it make sense?" For example, rule **BR-CO-16**: *amount due must equal total incl. VAT − amount already paid + rounding.*

## Folder layout

| Path | What it is |
|---|---|
| `config/scenarios.xml` | **Our** configuration: which rules apply to which invoice type (heavily commented) |
| `scripts/fetch-dependencies.sh` | Downloads the validator + official rules at **pinned versions** and verifies checksums |
| `Dockerfile` | Recipe for the image (non-root user, pinned base image, health check) |
| `docker-compose.yml` | How to run it (local-only port, read-only filesystem, memory limit) |
| `scripts/run-tests.sh` | Automated tests: valid invoices must pass, broken ones must fail for the right reason |
| `scripts/benchmark.sh` | Speed test |
| `samples/` | Test invoices (official KoSIT test cases + ones we deliberately broke). See `samples/NOTICE.md` |
| `vendor/` | Downloaded third-party files (not committed to git; recreate with the fetch script) |

## Run it yourself (exact commands)

You need: **Docker Desktop** (running), **Git**, and a terminal. On Windows use **Git Bash** or **WSL**.

```bash
cd validator
```

1. Download the validator and the rules (about 15 MB; checks every file):

```bash
bash scripts/fetch-dependencies.sh
```

2. Build the image and start the container in the background:

```bash
docker compose up -d --build
```

3. Check it's running. Wait until STATUS says `(healthy)`, about 10–40 s:

```bash
docker compose ps
```

4. Run the automated tests. Expect `Passed: 6   Failed: 0`:

```bash
bash scripts/run-tests.sh
```

5. Validate one invoice by hand and see the full report:

```bash
curl -X POST -H "Content-Type: application/xml" --data-binary @samples/invalid/wrong-payable-amount-ubl.xml http://127.0.0.1:8080/my-invoice.xml
```

6. Speed test (optional):

```bash
bash scripts/benchmark.sh 200 4
```

7. Look at the logs:

```bash
docker compose logs -f validator
```

8. Stop everything:

```bash
docker compose down
```

You can also open http://127.0.0.1:8080 in your browser: the validator has a simple demo page with an upload form.

## Verified results (2026-11-01, run in the cloud dev environment)

| Test | Result |
|---|---|
| Dependency download, all checksums/commits verified | ✅ |
| Image builds; container reports `healthy` | ✅ |
| `run-tests.sh`: 2 valid samples accepted, 3 broken samples rejected for the right reason (BR-CO-16, schema error, unknown document) | ✅ 6/6 |
| All **66** official XRechnung "standard" business-case invoices (UBL + CII) | ✅ 66/66 accepted in 1.9 s total |
| 20 XRechnung "extension" / technical cases | 16 accepted, 4 rejected: exactly the rules (BR-CL-13, BR-CL-21, BR-CO-16) that the official German configuration deliberately relaxes for those variants. Expected, because we only run the EU core rules. |
| Runs as non-root user (uid 999), read-only filesystem, all capabilities dropped | ✅ verified inside the container |
| Malformed XML → 422; empty body → 400; XXE attack (`<!DOCTYPE>` file read) → blocked, 422 | ✅ |
| 30 MB junk file → handled (406) in 1.9 s, container stayed healthy | ✅, but see limitations |
| Survives `docker compose restart` | ✅ |

**Speed** (container limited to 1 CPU / 768 MB, small 6.7 KB invoice, after warm-up):
- One at a time: median **10 ms**, p95 55 ms
- 4 at a time: ~**87 invoices/second**, median 18 ms
- Memory: ~205 MB

*Business meaning:* the Phase 1 report assumed 0.2–1.0 s of CPU per document. Measured validation is roughly 20–100× cheaper than that. Generating PDF/A-3 hybrid invoices is not tested yet and will be slower.

## Known limitations (honest list)

1. **EU core rules only.** German-specific XRechnung rules (BR-DE-*) and their relaxations are not included yet. Their official download host (`projekte.kosit.org`) is blocked by the cloud environment's network policy. On your own computer it should work. **XRechnung compliance cannot be claimed until those are added.**
2. **No authentication.** The validator itself has no API keys. That's why compose binds it to `127.0.0.1` only. Our real API (Phase 5) will sit in front of it and handle keys, rate limits and usage tracking.
3. **No upload size limit** in the validator. Our API layer must enforce one (e.g. 10 MB).
4. **Validation only.** No invoice *generation*, no PDF (Factur-X/ZUGFeRD) handling yet.
5. The validator's HTTP server is the simple built-in JDK server; KoSIT itself notes it's not meant for heavy production load. In the product it runs behind our own API, never exposed directly.

## Licences of included/downloaded parts

- KoSIT Validator: Apache 2.0
- KoSIT configuration files (report stylesheets, UBL XSD copies): Apache 2.0
- EN 16931 validation artefacts (CEN / ConnectingEurope): **EUPL 1.2**. If we *modify* these rules and offer them as a service, we must publish our modifications. We use them unmodified.
- UBL 2.1 schemas: OASIS
- Our own files (scenarios.xml, scripts, Dockerfile): project licence
