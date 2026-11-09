"""
API keys.

A key looks like  ifk_live_3s8F...  and is shown to the customer exactly once.
We store only its SHA-256 hash, like a password: if the database ever leaked,
the keys inside it could not be used. Customers send the key in a header:

    Authorization: Bearer ifk_live_...      (preferred)
    X-API-Key: ifk_live_...                 (also accepted)

RapidAPI marketplace: RapidAPI authenticates its own customers and forwards their calls
to us with three headers: X-RapidAPI-Proxy-Secret (proves the call came through RapidAPI),
X-RapidAPI-User (the customer's RapidAPI username) and X-RapidAPI-Subscription (their tier).
These headers are trusted ONLY when RAPIDAPI_PROXY_SECRET is configured and matches.
"""
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass

from fastapi import Request

from .config import settings
from .db import connection
from .errors import APIError
from .plans import Plan, get_plan

KEY_PREFIX = "ifk_live_"


@dataclass(frozen=True)
class Caller:
    key_id: int | None      # None for RapidAPI customers (RapidAPI holds their keys)
    customer_id: int
    email: str
    plan: Plan
    channel: str = "direct"  # "direct" or "rapidapi"
    tier: str | None = None  # RapidAPI subscription tier (BASIC, PRO, ULTRA, MEGA, CUSTOM)


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_key() -> tuple[str, str, str]:
    """Returns (raw key to show once, hash to store, short prefix for display)."""
    raw = KEY_PREFIX + secrets.token_urlsafe(32)
    return raw, hash_key(raw), raw[: len(KEY_PREFIX) + 4]


def issue_key(conn, customer_id: int, label: str | None = None) -> str:
    raw, digest, prefix = new_key()
    conn.execute("INSERT INTO api_keys (customer_id, key_hash, key_prefix, label) VALUES (%s, %s, %s, %s)",
                 (customer_id, digest, prefix, label))
    return raw


def _key_from_headers(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return request.headers.get("x-api-key", "").strip() or None


def _rapidapi_caller(request: Request) -> Caller | None:
    sent = request.headers.get("x-rapidapi-proxy-secret")
    if not settings.rapidapi_proxy_secret or sent is None:
        return None  # integration off, or not a RapidAPI call
    if not hmac.compare_digest(sent.encode(), settings.rapidapi_proxy_secret.encode()):
        raise APIError(403, "invalid_proxy_secret", "Request did not come through the RapidAPI gateway.")
    user = request.headers.get("x-rapidapi-user", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,100}", user):
        raise APIError(400, "missing_rapidapi_user", "RapidAPI user header is missing or invalid.")
    tier = re.sub(r"[^A-Za-z0-9_-]", "", request.headers.get("x-rapidapi-subscription", ""))[:20] or None
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO customers (email, plan, notes) VALUES (%s, 'rapidapi', 'RapidAPI marketplace')
               ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
               RETURNING id, email, plan""", (f"rapidapi:{user}",)).fetchone()
    caller = Caller(None, row["id"], row["email"], get_plan(row["plan"]), "rapidapi", tier)
    request.state.caller = caller
    return caller


def authenticate(request: Request) -> Caller:
    rapid = _rapidapi_caller(request)
    if rapid is not None:
        return rapid
    raw = _key_from_headers(request)
    if not raw:
        raise APIError(401, "missing_api_key", "Send your API key as 'Authorization: Bearer <key>'.",
                       headers={"WWW-Authenticate": "Bearer"})
    with connection() as conn:
        row = conn.execute(
            """SELECT k.id AS key_id, c.id AS customer_id, c.email, c.plan
                 FROM api_keys k JOIN customers c ON c.id = k.customer_id
                WHERE k.key_hash = %s AND k.revoked_at IS NULL""", (hash_key(raw),)).fetchone()
    if row is None:
        raise APIError(401, "invalid_api_key", "This API key is not valid or has been revoked.",
                       headers={"WWW-Authenticate": "Bearer"})
    caller = Caller(row["key_id"], row["customer_id"], row["email"], get_plan(row["plan"]))
    request.state.caller = caller
    return caller
