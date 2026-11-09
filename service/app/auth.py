"""
API keys.

A key looks like  ifk_live_3s8F...  and is shown to the customer exactly once.
We store only its SHA-256 hash, like a password: if the database ever leaked,
the keys inside it could not be used. Customers send the key in a header:

    Authorization: Bearer ifk_live_...      (preferred)
    X-API-Key: ifk_live_...                 (also accepted)
"""
import hashlib
import secrets
from dataclasses import dataclass

from fastapi import Request

from .db import connection
from .errors import APIError
from .plans import Plan, get_plan

KEY_PREFIX = "ifk_live_"


@dataclass(frozen=True)
class Caller:
    key_id: int
    customer_id: int
    email: str
    plan: Plan


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


def authenticate(request: Request) -> Caller:
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
