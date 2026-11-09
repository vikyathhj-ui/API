"""
Pricing plans. One "document" = one successful call to generate or validate.
Change prices/quotas here; the landing page and /v1/usage read from this table.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    price_usd_month: int
    documents_per_month: int
    requests_per_minute: int


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Free", 0, 50, 10),
    "starter": Plan("starter", "Starter", 19, 500, 60),
    "growth": Plan("growth", "Growth", 79, 5_000, 120),
    "scale": Plan("scale", "Scale", 249, 30_000, 300),
}


def get_plan(plan_id: str) -> Plan:
    return PLANS.get(plan_id, PLANS["free"])
