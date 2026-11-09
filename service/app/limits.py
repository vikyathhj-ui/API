"""
Protection against abuse and runaway costs:

* Rate limit  - requests per minute per API key, counted in Redis (fast, in memory).
* Quota       - documents per calendar month per customer, counted in PostgreSQL
                (the source of truth for billing).
* Usage log   - one row per call: endpoint, status, duration. Never invoice contents.

If Redis is down we let requests through (and log it) rather than take the whole
API offline; the monthly quota in PostgreSQL still caps total usage.
"""
import logging
import time

import redis

from .auth import Caller
from .config import settings
from .db import connection
from .errors import APIError

log = logging.getLogger("app.limits")
_redis = redis.Redis.from_url(settings.redis_url, socket_timeout=0.5, socket_connect_timeout=0.5)


def redis_client() -> redis.Redis:
    return _redis


def check_rate_limit(caller: Caller) -> dict:
    limit = caller.plan.requests_per_minute
    window = int(time.time() // 60)
    key = f"rl:{caller.key_id}:{window}"
    try:
        pipe = _redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 120)
        count = pipe.execute()[0]
    except redis.RedisError:
        log.warning("redis unavailable: rate limit not enforced")
        return {}
    retry_after = 60 - int(time.time()) % 60
    headers = {"X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": str(max(0, limit - count))}
    if count > limit:
        raise APIError(429, "rate_limited",
                       f"Too many requests: your plan allows {limit} per minute.",
                       {"limit_per_minute": limit, "retry_after_seconds": retry_after},
                       headers={**headers, "Retry-After": str(retry_after)})
    return headers


def documents_used_this_month(customer_id: int) -> int:
    with connection() as conn:
        row = conn.execute(
            """SELECT count(*) AS n FROM usage_events
                WHERE customer_id = %s AND billable AND created_at >= date_trunc('month', now())""",
            (customer_id,)).fetchone()
    return int(row["n"])


def check_quota(caller: Caller) -> dict:
    used = documents_used_this_month(caller.customer_id)
    quota = caller.plan.documents_per_month
    headers = {"X-Quota-Limit": str(quota), "X-Quota-Used": str(used)}
    if used >= quota:
        raise APIError(429, "quota_exceeded",
                       f"Monthly quota reached: {used} of {quota} documents on the "
                       f"{caller.plan.name} plan. Upgrade to continue this month.",
                       {"used": used, "quota": quota, "plan": caller.plan.id}, headers=headers)
    return headers


def record_usage(caller: Caller, endpoint: str, status: int, billable: bool, duration_ms: int) -> None:
    try:
        with connection() as conn:
            conn.execute(
                """INSERT INTO usage_events (customer_id, api_key_id, endpoint, status, billable, duration_ms)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (caller.customer_id, caller.key_id, endpoint, status, billable, duration_ms))
    except Exception:  # usage logging must never break a customer's request
        log.exception("failed to record usage")


def check_signup_limit(ip: str) -> None:
    key = f"signup:{ip}:{int(time.time() // 3600)}"
    try:
        pipe = _redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3700)
        count = pipe.execute()[0]
    except redis.RedisError:
        log.warning("redis unavailable: signup limit not enforced")
        return
    if count > settings.signups_per_ip_per_hour:
        raise APIError(429, "too_many_signups", "Too many sign-ups from this network. Try again later.")
