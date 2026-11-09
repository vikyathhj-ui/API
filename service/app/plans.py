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
    public: bool = True        # shown on the website's pricing table


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Free", 0, 50, 10),
    "starter": Plan("starter", "Starter", 19, 500, 60),
    "growth": Plan("growth", "Growth", 79, 5_000, 120),
    "scale": Plan("scale", "Scale", 249, 30_000, 300),
    # Customers who subscribe through the RapidAPI marketplace. RapidAPI enforces their
    # quota and bills them; we only keep a generous safety limit and count usage.
    "rapidapi": Plan("rapidapi", "RapidAPI", 0, 10_000_000, 300, public=False),
}


def get_plan(plan_id: str) -> Plan:
    return PLANS.get(plan_id, PLANS["free"])
