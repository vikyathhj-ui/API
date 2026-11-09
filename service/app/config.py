"""
All settings come from environment variables, so the same Docker image runs
locally and in production. Secrets (the database password) are never written
in code: they live in the .env file (not committed to git) or the host's secret store.
"""
import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    validator_url: str
    max_body_bytes: int
    signup_enabled: bool
    signups_per_ip_per_hour: int
    product_name: str
    contact_email: str
    public_base_url: str
    payment_links: dict


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/invoiceformat"),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        validator_url=os.environ.get("VALIDATOR_URL", "http://localhost:8080").rstrip("/"),
        max_body_bytes=int(os.environ.get("MAX_BODY_BYTES", str(10 * 1024 * 1024))),
        signup_enabled=_bool("SIGNUP_ENABLED", True),
        signups_per_ip_per_hour=int(os.environ.get("SIGNUPS_PER_IP_PER_HOUR", "3")),
        product_name=os.environ.get("PRODUCT_NAME", "InvoiceFormat API"),
        contact_email=os.environ.get("CONTACT_EMAIL", ""),
        public_base_url=os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/"),
        # Optional checkout links from your payment provider, one per paid plan
        payment_links={p: os.environ.get(f"PAYMENT_LINK_{p.upper()}", "").strip()
                       for p in ("starter", "growth", "scale")},
    )


settings = load_settings()
