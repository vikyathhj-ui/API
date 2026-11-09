"""
Integration tests for the HTTP API. They need the real database, Redis and validator,
so run them inside the running stack:

    docker compose exec api pytest -q

Each test creates its own customer, so tests don't interfere with each other.
"""
import base64
import io
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from app import db
from app.auth import issue_key
from app.main import app

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = json.loads((ROOT / "samples" / "fr-consulting.json").read_text(encoding="utf-8"))
NS = {"ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"}


def _ip() -> tuple[str, int]:
    return (f"10.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}", 50000)


@pytest.fixture(scope="module")
def client():
    with TestClient(app, client=_ip()) as c:  # "with" runs start-up (schema creation)
        yield c


def make_customer(plan="free") -> tuple[int, str]:
    with db.connection() as conn:
        cid = conn.execute("INSERT INTO customers (email, plan) VALUES (%s, %s) RETURNING id",
                           (f"test-{uuid.uuid4().hex[:12]}@example.com", plan)).fetchone()["id"]
        key = issue_key(conn, cid, "test")
    return cid, key


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def billable_count(cid) -> int:
    with db.connection() as conn:
        return conn.execute("SELECT count(*) AS n FROM usage_events WHERE customer_id=%s AND billable",
                            (cid,)).fetchone()["n"]


# ---------------------------------------------------------------- service
def test_health(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["checks"] == {"database": "ok", "cache": "ok", "validator": "ok"}


def test_home_page_and_security_headers(client):
    r = client.get("/")
    assert r.status_code == 200 and "Pricing" in r.text and "$19" in r.text
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert client.get("/terms").status_code == 200 and client.get("/privacy").status_code == 200
    assert client.get("/openapi.json").json()["info"]["version"] == "1.0.0"


# ---------------------------------------------------------------- auth
def test_missing_and_invalid_keys(client):
    r = client.post("/v1/invoices", json=SAMPLE)
    assert r.status_code == 401 and r.json()["error"]["code"] == "missing_api_key"
    r = client.post("/v1/invoices", json=SAMPLE, headers=auth("ifk_live_nope"))
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_api_key"


def test_revoked_key_and_x_api_key_header(client):
    cid, key = make_customer()
    assert client.get("/v1/usage", headers={"X-API-Key": key}).status_code == 200
    with db.connection() as conn:
        conn.execute("UPDATE api_keys SET revoked_at = now() WHERE customer_id = %s", (cid,))
    assert client.get("/v1/usage", headers=auth(key)).status_code == 401


# ---------------------------------------------------------------- generate
def test_generate_pdf(client):
    cid, key = make_customer()
    r = client.post("/v1/invoices", json=SAMPLE, headers=auth(key))
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF-")
    assert r.headers["content-disposition"] == 'attachment; filename="FA-2026-0042.pdf"'
    assert r.headers["x-invoice-total"] == "1495.79 EUR"
    assert r.headers["x-quota-used"] == "1" and r.headers["x-quota-limit"] == "50"
    assert billable_count(cid) == 1


def test_generate_json_and_xml(client):
    _, key = make_customer()
    r = client.post("/v1/invoices?format=json", json=SAMPLE, headers=auth(key))
    body = r.json()
    assert body["totals"] == {"net": "1246.49", "vat": "249.30", "gross": "1495.79", "due": "1495.79"}
    assert base64.b64decode(body["pdf_base64"]).startswith(b"%PDF-")
    root = etree.fromstring(body["xml"].encode())
    assert root.find(".//ram:DuePayableAmount", NS).text == "1495.79"
    r = client.post("/v1/invoices?format=xml", json=SAMPLE, headers=auth(key))
    assert r.headers["content-type"].startswith("application/xml") and b"CrossIndustryInvoice" in r.content


def test_generate_invalid_input_is_not_billed(client):
    cid, key = make_customer()
    bad = json.loads(json.dumps(SAMPLE)); del bad["invoice"]["delivery_date"]
    r = client.post("/v1/invoices", json=bad, headers=auth(key))
    assert r.status_code == 400
    assert r.json()["error"] == {"code": "invalid_invoice", "message": "invoice.delivery_date is required"}
    r = client.post("/v1/invoices", content=b"not json", headers={**auth(key), "Content-Type": "application/json"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_request"
    assert billable_count(cid) == 0


# ---------------------------------------------------------------- validate
@pytest.fixture(scope="module")
def generated(client):
    _, key = make_customer("starter")
    body = client.post("/v1/invoices?format=json", json=SAMPLE, headers=auth(key)).json()
    return base64.b64decode(body["pdf_base64"]), body["xml"].encode()


def test_validate_valid_pdf_and_xml(client, generated):
    cid, key = make_customer()
    pdf, xml = generated
    r = client.post("/v1/validate", content=pdf, headers={**auth(key), "Content-Type": "application/pdf"})
    body = r.json()
    assert r.status_code == 200 and body["valid"] is True and body["source"] == "pdf"
    assert body["format"] == "EN16931 core (CII)" and body["errors"] == []
    r = client.post("/v1/validate", content=xml, headers={**auth(key), "Content-Type": "application/xml"})
    assert r.json()["valid"] is True and r.json()["source"] == "xml"
    assert billable_count(cid) == 2


def test_validate_reports_errors_with_hints(client, generated):
    _, key = make_customer()
    broken = generated[1].replace(b"<ram:DuePayableAmount>1495.79<", b"<ram:DuePayableAmount>1500.00<")
    body = client.post("/v1/validate", content=broken, headers=auth(key)).json()
    assert body["valid"] is False
    rules = {e["rule"]: e for e in body["errors"]}
    assert "BR-CO-16" in rules and "rounding" in rules["BR-CO-16"]["hint"]


def test_validate_bad_inputs(client):
    cid, key = make_customer()
    r = client.post("/v1/validate", content=b"hello", headers=auth(key))
    assert r.status_code == 415 and r.json()["error"]["code"] == "unsupported_document"
    r = client.post("/v1/validate", content=b"%PDF-1.7 not really", headers=auth(key))
    assert r.status_code == 422 and r.json()["error"]["code"] == "no_embedded_invoice"
    r = client.post("/v1/validate", content=b"<Invoice><broken>", headers=auth(key))
    assert r.status_code == 200 and r.json()["valid"] is False
    xxe = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>'
    r = client.post("/v1/validate", content=xxe, headers=auth(key))
    assert r.json()["valid"] is False and "root:" not in r.text
    r = client.post("/v1/validate", content=b"", headers=auth(key))
    assert r.status_code == 400
    # Only the malformed-but-processed documents count (2), not the rejected requests.
    assert billable_count(cid) == 2


# ---------------------------------------------------------------- limits
def test_usage_endpoint(client):
    _, key = make_customer("growth")
    client.post("/v1/invoices?format=xml", json=SAMPLE, headers=auth(key))
    u = client.get("/v1/usage", headers=auth(key)).json()
    assert u["plan"]["id"] == "growth" and u["documents_used"] == 1 and u["documents_remaining"] == 4999


def test_rate_limit(client):
    _, key = make_customer("free")  # 10 requests per minute
    codes = [client.post("/v1/invoices", json={}, headers=auth(key)).status_code for _ in range(11)]
    if codes[-1] != 429:  # the minute rolled over mid-test: retry once in a fresh window
        codes = [client.post("/v1/invoices", json={}, headers=auth(key)).status_code for _ in range(11)]
    assert codes[:10] == [400] * 10 and codes[10] == 429
    r = client.post("/v1/invoices", json={}, headers=auth(key))
    assert r.json()["error"]["code"] == "rate_limited" and int(r.headers["retry-after"]) <= 60


def test_monthly_quota(client):
    cid, key = make_customer("free")
    with db.connection() as conn:
        conn.execute("""INSERT INTO usage_events (customer_id, endpoint, status, billable, duration_ms)
                        SELECT %s, 'invoices', 200, true, 1 FROM generate_series(1, 50)""", (cid,))
    r = client.post("/v1/invoices", json=SAMPLE, headers=auth(key))
    assert r.status_code == 429 and r.json()["error"]["code"] == "quota_exceeded"
    assert r.json()["error"]["details"] == {"used": 50, "quota": 50, "plan": "free"}


def test_size_limits(client):
    _, key = make_customer()
    r = client.post("/v1/validate", content=b"<" + b"a" * (10 * 1024 * 1024 + 1), headers=auth(key))
    assert r.status_code == 413 and r.json()["error"]["code"] == "payload_too_large"
    r = client.post("/v1/validate", content=iter([b"<x/>"]), headers=auth(key))  # chunked, no length
    assert r.status_code == 411


# ---------------------------------------------------------------- signup
def test_signup_flow():
    with TestClient(app, client=_ip()) as c:
        email = f"new-{uuid.uuid4().hex[:8]}@example.com"
        r = c.post("/v1/signup", json={"email": email, "name": "Ada"})
        assert r.status_code == 201 and r.json()["api_key"].startswith("ifk_live_")
        assert c.get("/v1/usage", headers=auth(r.json()["api_key"])).json()["plan"]["id"] == "free"
        assert c.post("/v1/signup", json={"email": email.upper()}).status_code == 409
        assert c.post("/v1/signup", json={"email": "not-an-email"}).json()["error"]["code"] == "invalid_email"
        codes = [c.post("/v1/signup", json={"email": f"x{i}-{uuid.uuid4().hex[:6]}@example.com"}).status_code
                 for i in range(3)]
        assert codes[-1] == 429  # 3 per hour per IP: the 4th successful-looking attempt is refused


def test_api_key_is_stored_hashed_and_invoice_content_is_not_stored(client):
    _, key = make_customer()
    client.post("/v1/invoices", json=SAMPLE, headers=auth(key))
    with db.connection() as conn:
        dump = json.dumps([conn.execute(f"SELECT * FROM {t}").fetchall()
                           for t in ("customers", "api_keys", "usage_events")], default=str)
    assert key not in dump
    assert "FA-2026-0042" not in dump and "Atelier Exemple" not in dump


# ---------------------------------------------------------------- RapidAPI marketplace
import dataclasses

import app.auth as auth_module
from app.config import settings as real_settings

RAPID_SECRET = "test-proxy-secret-1234567890"


@pytest.fixture
def rapidapi_on(monkeypatch):
    monkeypatch.setattr(auth_module, "settings",
                        dataclasses.replace(real_settings, rapidapi_proxy_secret=RAPID_SECRET))


def rapid_headers(user, secret=RAPID_SECRET, tier="PRO"):
    return {"X-RapidAPI-Proxy-Secret": secret, "X-RapidAPI-User": user,
            "X-RapidAPI-Subscription": tier, "X-RapidAPI-Host": "einvoice.p.rapidapi.com"}


def test_rapidapi_call_creates_customer_and_counts_usage(client, rapidapi_on):
    user = f"rapiduser{uuid.uuid4().hex[:8]}"
    for _ in range(2):
        r = client.post("/v1/invoices?format=xml", json=SAMPLE, headers=rapid_headers(user))
        assert r.status_code == 200, r.text
    with db.connection() as conn:
        c = conn.execute("SELECT id, plan FROM customers WHERE email = %s", (f"rapidapi:{user}",)).fetchone()
        rows = conn.execute("SELECT api_key_id, billable FROM usage_events WHERE customer_id = %s",
                            (c["id"],)).fetchall()
    assert c["plan"] == "rapidapi"
    assert len(rows) == 2 and all(r["billable"] and r["api_key_id"] is None for r in rows)
    r = client.post("/v1/validate", content=b"<x/>", headers=rapid_headers(user))
    assert r.status_code == 200 and r.json()["valid"] is False


def test_rapidapi_wrong_secret_and_missing_user(client, rapidapi_on):
    r = client.post("/v1/invoices", json=SAMPLE, headers=rapid_headers("someone", secret="wrong"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "invalid_proxy_secret"
    r = client.post("/v1/invoices", json=SAMPLE, headers=rapid_headers(""))
    assert r.status_code == 400 and r.json()["error"]["code"] == "missing_rapidapi_user"


def test_rapidapi_headers_ignored_when_not_configured(client, monkeypatch):
    # Integration off (no secret configured): faking RapidAPI headers must not grant access.
    monkeypatch.setattr(auth_module, "settings", dataclasses.replace(real_settings, rapidapi_proxy_secret=""))
    r = client.post("/v1/invoices", json=SAMPLE, headers=rapid_headers("attacker", secret="anything"))
    assert r.status_code == 401 and r.json()["error"]["code"] == "missing_api_key"


def test_rapidapi_plan_hidden_and_reserved_emails(client):
    assert "RapidAPI" not in client.get("/").text.split('id="pricing"')[1].split('id="signup"')[0]
    with TestClient(app, client=_ip()) as c:
        r = c.post("/v1/signup", json={"email": "rapidapi:bob@example.com"})
        assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_email"
