"""
InvoiceFormat API: the web application.

Endpoints (all JSON unless noted):
  POST /v1/invoices          JSON invoice -> Factur-X/ZUGFeRD PDF (or JSON/XML)   [API key]
  POST /v1/validate          XML or Factur-X PDF -> validation report            [API key]
  GET  /v1/usage             your plan, quota and usage this month                [API key]
  POST /v1/signup            email -> free API key (shown once)
  GET  /v1/health            is the service working?
  GET  /docs                 interactive API documentation
  GET  /                     landing page
"""
import base64
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import Body, Depends, FastAPI, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from jinja2 import Environment, FileSystemLoader, select_autoescape
from psycopg.errors import UniqueViolation

from . import db
from .auth import Caller, authenticate, issue_key
from .config import settings
from .errors import APIError, error_body, install_handlers
from .invoice.generator import InvoiceInputError, generate
from .limits import (check_quota, check_rate_limit, check_signup_limit, documents_used_this_month,
                     record_usage, redis_client)
from .plans import PLANS
from .validation import LIMITATIONS, RULESET, extract_xml, validate_xml, validator_healthy

VERSION = "1.0.0"
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await run_in_threadpool(db.init_schema)
    yield
    db.close()


app = FastAPI(
    title=settings.product_name, version=VERSION, lifespan=lifespan, redoc_url=None, docs_url=None,
    description=(
        "Create and validate EU e-invoices (EN 16931) with one API call.\n\n"
        "* **Generate** a Factur-X / ZUGFeRD PDF (PDF/A-3 with embedded XML) from simple JSON. "
        "We calculate all totals and VAT for you.\n"
        "* **Validate** an XML (UBL or CII) or Factur-X/ZUGFeRD PDF and get errors explained in plain English.\n\n"
        "**Authentication:** `Authorization: Bearer <your API key>`. Get a free key on the home page.\n\n"
        "**Privacy:** invoice contents are processed in memory and never stored.\n\n"
        "*Technical format generation and validation only; not tax or legal advice.*"),
)
install_handlers(app)
# Docs page assets are served by us (no third-party CDN: works offline, pinned version, no tracking).
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")
bearer = HTTPBearer(auto_error=False, description="Your API key, e.g. ifk_live_...")  # for the docs' Authorize button
_templates = Environment(loader=FileSystemLoader(Path(__file__).parent / "web"),
                         autoescape=select_autoescape(["html"]))
SAMPLE = json.loads((Path(__file__).parent / "invoice" / "example_invoice.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Middleware: request id, size limit, security headers, access log
# --------------------------------------------------------------------------- #
@app.middleware("http")
async def frame(request: Request, call_next):
    request_id = uuid.uuid4().hex[:16]
    request.state.request_id = request_id
    started = time.perf_counter()
    if request.method in ("POST", "PUT", "PATCH"):
        length = request.headers.get("content-length")
        if length is None:
            resp = JSONResponse(error_body("length_required", "Send a Content-Length header."), status_code=411)
            return _finish(request, resp, started)
        if not length.isdigit() or int(length) > settings.max_body_bytes:
            resp = JSONResponse(error_body("payload_too_large",
                                           f"Maximum request size is {settings.max_body_bytes // (1024 * 1024)} MB."),
                                status_code=413)
            return _finish(request, resp, started)
    response = await call_next(request)
    return _finish(request, response, started)


def _finish(request: Request, response: Response, started: float) -> Response:
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    caller = getattr(request.state, "caller", None)
    # Access log: never the body, never the API key.
    log.info(json.dumps({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "id": request.state.request_id, "method": request.method,
                         "path": request.url.path, "status": response.status_code,
                         "ms": round((time.perf_counter() - started) * 1000),
                         "customer": caller.customer_id if caller else None}))
    return response


def _guard(request: Request) -> tuple[Caller, dict]:
    caller = authenticate(request)
    headers = check_rate_limit(caller)
    headers.update(check_quota(caller))
    return caller, headers


def _safe_filename(number: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._-]", "_", number)[:80] or "invoice") + ".pdf"


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@app.post("/v1/invoices", tags=["Invoices"], dependencies=[Depends(bearer)],
          summary="Create a Factur-X / ZUGFeRD e-invoice",
          responses={200: {"content": {"application/pdf": {}, "application/xml": {}, "application/json": {}},
                           "description": "The e-invoice (PDF by default)."},
                     400: {"description": "The invoice data is incomplete or wrong (not counted)."}})
def create_invoice(
    request: Request,
    invoice: dict = Body(..., openapi_examples={"french_invoice": {"summary": "French B2B invoice",
                                                                    "value": SAMPLE}}),
    format: Literal["pdf", "json", "xml"] = Query(
        "pdf", description="pdf = Factur-X PDF file; xml = the CII XML only; "
                           "json = totals + XML + base64 PDF in one JSON object"),
):
    """Send invoice data as JSON. **Do not send totals**: we calculate line totals, VAT per rate
    and the amount due, so arithmetic errors cannot happen. Profile: Factur-X / ZUGFeRD EN 16931."""
    caller, headers = _guard(request)
    started = time.perf_counter()
    try:
        pdf, xml, inv = generate(invoice)
    except InvoiceInputError as e:
        record_usage(caller, "invoices", 400, False, _ms(started))
        raise APIError(400, "invalid_invoice", str(e), headers=headers)
    record_usage(caller, "invoices", 200, True, _ms(started))
    headers["X-Quota-Used"] = str(int(headers.get("X-Quota-Used", "0")) + 1)
    headers["X-Invoice-Total"] = f"{inv.grand_total} {inv.currency}"

    if format == "xml":
        return Response(xml, media_type="application/xml", headers=headers)
    if format == "json":
        return JSONResponse(headers=headers, content={
            "invoice_number": inv.number, "profile": "factur-x-en16931", "currency": inv.currency,
            "totals": {"net": str(inv.line_total), "vat": str(inv.tax_total),
                       "gross": str(inv.grand_total), "due": str(inv.due_amount)},
            "vat_breakdown": [{"rate": str(g.rate), "taxable": str(g.basis), "vat": str(g.tax)}
                              for g in inv.vat_groups],
            "xml": xml.decode("utf-8"), "pdf_base64": base64.b64encode(pdf).decode("ascii")})
    headers["Content-Disposition"] = f'attachment; filename="{_safe_filename(inv.number)}"'
    return Response(pdf, media_type="application/pdf", headers=headers)


@app.post("/v1/validate", tags=["Validation"], dependencies=[Depends(bearer)],
          summary="Validate an e-invoice (XML or Factur-X/ZUGFeRD PDF)",
          openapi_extra={"requestBody": {"required": True, "content": {
              "application/xml": {"schema": {"type": "string"}},
              "application/pdf": {"schema": {"type": "string", "format": "binary"}}}}})
async def validate(request: Request):
    """Send the raw file as the request body. Returns `valid` plus errors and warnings, each with the
    rule ID, message, location and (for common rules) a plain-English `hint`. A processed document
    always returns HTTP 200; check the `valid` field."""
    caller, headers = await run_in_threadpool(_guard, request)
    body = await request.body()
    started = time.perf_counter()
    if not body:
        await run_in_threadpool(record_usage, caller, "validate", 400, False, _ms(started))
        raise APIError(400, "empty_body", "Send the invoice file as the request body.", headers=headers)
    try:
        xml, source = extract_xml(body)
        report = await run_in_threadpool(validate_xml, xml)
    except APIError as e:
        billable = False
        await run_in_threadpool(record_usage, caller, "validate", e.status, billable, _ms(started))
        e.headers = {**headers, **(e.headers or {})}
        raise
    await run_in_threadpool(record_usage, caller, "validate", 200, True, _ms(started))
    headers["X-Quota-Used"] = str(int(headers.get("X-Quota-Used", "0")) + 1)
    return JSONResponse({"valid": report["valid"], "source": source, **{k: v for k, v in report.items()
                                                                       if k != "valid"}},
                        headers=headers)


@app.get("/v1/usage", tags=["Account"], dependencies=[Depends(bearer)], summary="Your plan and usage")
def usage(request: Request):
    caller = authenticate(request)
    used = documents_used_this_month(caller.customer_id)
    now = datetime.now(timezone.utc)
    p = caller.plan
    return {"plan": {"id": p.id, "name": p.name, "price_usd_month": p.price_usd_month,
                     "documents_per_month": p.documents_per_month,
                     "requests_per_minute": p.requests_per_minute},
            "period_start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "documents_used": used, "documents_remaining": max(0, p.documents_per_month - used)}


@app.post("/v1/signup", tags=["Account"], status_code=201, summary="Get a free API key")
def signup(request: Request, payload: dict = Body(..., examples=[{"email": "dev@example.com", "name": "Ada"}])):
    """Creates a Free-plan account and returns an API key **once**. Store it safely."""
    if not settings.signup_enabled:
        raise APIError(403, "signup_disabled", "Self-service sign-up is currently closed. Please contact us.")
    email = str(payload.get("email", "")).strip().lower()
    # No ":" allowed: "rapidapi:<user>" is reserved for RapidAPI marketplace customers.
    if not re.fullmatch(r"[^@\s:]{1,64}@[^@\s:]{1,190}\.[A-Za-z]{2,24}", email):
        raise APIError(400, "invalid_email", "Please enter a valid email address.")
    name = str(payload.get("name", "")).strip()[:120] or None
    check_signup_limit(request.client.host if request.client else "unknown")
    try:
        with db.connection() as conn:
            row = conn.execute("INSERT INTO customers (email, name, plan) VALUES (%s, %s, 'free') RETURNING id",
                               (email, name)).fetchone()
            key = issue_key(conn, row["id"], "signup")
    except UniqueViolation:
        raise APIError(409, "email_already_registered",
                       "This email already has an account. Contact support if you lost your key.")
    log.info(json.dumps({"event": "signup", "customer": row["id"]}))
    free = PLANS["free"]
    return {"api_key": key, "plan": free.id, "documents_per_month": free.documents_per_month,
            "message": "Save this key now: it will not be shown again."}


@app.api_route("/v1/health", methods=["GET", "HEAD"], tags=["Service"], summary="Service health")
def health():
    checks = {}
    try:
        with db.connection() as conn:
            conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    try:
        redis_client().ping()
        checks["cache"] = "ok"
    except Exception:
        checks["cache"] = "down"
    checks["validator"] = "ok" if validator_healthy() else "down"
    # Redis down only weakens rate limiting; database or validator down breaks the service.
    ok = checks["database"] == "ok" and checks["validator"] == "ok"
    return JSONResponse({"status": "ok" if ok else "degraded", "version": VERSION, "checks": checks},
                        status_code=200 if ok else 503)


# --------------------------------------------------------------------------- #
# Website
# --------------------------------------------------------------------------- #
def _page(name: str) -> HTMLResponse:
    html = _templates.get_template(name).render(
        product=settings.product_name, plans=[p for p in PLANS.values() if p.public], contact=settings.contact_email,
        payment_links=settings.payment_links, signup_enabled=settings.signup_enabled,
        base_url=settings.public_base_url, ruleset=RULESET, limitations=LIMITATIONS,
        example=json.dumps(SAMPLE, indent=2, ensure_ascii=False), year=datetime.now(timezone.utc).year)
    resp = HTMLResponse(html)
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                               "script-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                                               "connect-src 'self'; frame-ancestors 'none'")
    return resp


@app.get("/docs", include_in_schema=False)
def docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{settings.product_name}: API docs",
                               swagger_js_url="/static/swagger/swagger-ui-bundle.js",
                               swagger_css_url="/static/swagger/swagger-ui.css", swagger_favicon_url="")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def home():
    return _page("index.html")


@app.get("/terms", include_in_schema=False)
def terms():
    return _page("terms.html")


@app.get("/privacy", include_in_schema=False)
def privacy():
    return _page("privacy.html")


def _ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)
