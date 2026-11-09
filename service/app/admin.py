"""
Admin command line, for you (the operator). Run inside the API container:

  docker compose exec api python -m app.admin list
  docker compose exec api python -m app.admin create --email buyer@company.com --plan starter --name "Company"
  docker compose exec api python -m app.admin set-plan --email buyer@company.com --plan growth
  docker compose exec api python -m app.admin new-key --email buyer@company.com
  docker compose exec api python -m app.admin revoke-key --prefix ifk_live_AbCd
  docker compose exec api python -m app.admin usage [--email buyer@company.com]

Typical sale: customer pays via your payment link -> you run `set-plan` (or `create`).
"""
import argparse
import sys

from . import db
from .auth import issue_key
from .plans import PLANS


def _customer(conn, email: str) -> dict:
    row = conn.execute("SELECT * FROM customers WHERE email = %s", (email.strip().lower(),)).fetchone()
    if row is None:
        sys.exit(f"No customer with email {email}")
    return row


def cmd_create(a):
    with db.connection() as conn:
        row = conn.execute("INSERT INTO customers (email, name, plan) VALUES (%s, %s, %s) RETURNING id",
                           (a.email.strip().lower(), a.name, a.plan)).fetchone()
        key = issue_key(conn, row["id"], "admin")
    print(f"Created customer #{row['id']} on plan '{a.plan}'.")
    print(f"API key (shown once, send it to the customer securely):\n{key}")


def cmd_set_plan(a):
    with db.connection() as conn:
        c = _customer(conn, a.email)
        conn.execute("UPDATE customers SET plan = %s WHERE id = %s", (a.plan, c["id"]))
    print(f"{a.email}: plan {c['plan']} -> {a.plan}")


def cmd_new_key(a):
    with db.connection() as conn:
        c = _customer(conn, a.email)
        key = issue_key(conn, c["id"], a.label)
    print(f"New API key for {a.email} (shown once):\n{key}")


def cmd_revoke(a):
    with db.connection() as conn:
        n = conn.execute("UPDATE api_keys SET revoked_at = now() WHERE key_prefix = %s AND revoked_at IS NULL",
                         (a.prefix,)).rowcount
    print(f"Revoked {n} key(s) with prefix {a.prefix}")


def cmd_list(_a):
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT c.id, c.email, c.plan, c.created_at::date AS since,
                      count(k.id) FILTER (WHERE k.revoked_at IS NULL) AS active_keys,
                      string_agg(k.key_prefix, ' ') FILTER (WHERE k.revoked_at IS NULL) AS prefixes
                 FROM customers c LEFT JOIN api_keys k ON k.customer_id = c.id
                GROUP BY c.id ORDER BY c.id""").fetchall()
    print(f"{'id':>4}  {'email':<34} {'plan':<8} {'since':<10} keys")
    for r in rows:
        print(f"{r['id']:>4}  {r['email']:<34} {r['plan']:<8} {str(r['since']):<10} "
              f"{r['active_keys']} {r['prefixes'] or ''}")


def cmd_usage(a):
    sql = """SELECT c.email, c.plan, count(u.id) FILTER (WHERE u.billable) AS documents,
                    count(u.id) FILTER (WHERE NOT u.billable) AS rejected,
                    coalesce(round(avg(u.duration_ms)), 0) AS avg_ms
               FROM customers c LEFT JOIN usage_events u
                 ON u.customer_id = c.id AND u.created_at >= date_trunc('month', now())
              WHERE (%s::text IS NULL OR c.email = %s)
              GROUP BY c.id ORDER BY documents DESC"""
    email = a.email.strip().lower() if a.email else None
    with db.connection() as conn:
        rows = conn.execute(sql, (email, email)).fetchall()
    print(f"Usage this month (UTC)\n{'email':<34} {'plan':<8} {'docs':>6} {'quota':>6} {'rejected':>8} {'avg ms':>7}")
    for r in rows:
        quota = PLANS.get(r["plan"], PLANS["free"]).documents_per_month
        print(f"{r['email']:<34} {r['plan']:<8} {r['documents']:>6} {quota:>6} {r['rejected']:>8} {r['avg_ms']:>7}")


def main():
    p = argparse.ArgumentParser(prog="python -m app.admin", description="InvoiceFormat API admin")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("create", help="create a customer and an API key")
    s.add_argument("--email", required=True); s.add_argument("--name")
    s.add_argument("--plan", choices=PLANS, default="free"); s.set_defaults(f=cmd_create)
    s = sub.add_parser("set-plan", help="change a customer's plan")
    s.add_argument("--email", required=True); s.add_argument("--plan", choices=PLANS, required=True)
    s.set_defaults(f=cmd_set_plan)
    s = sub.add_parser("new-key", help="issue an extra API key"); s.add_argument("--email", required=True)
    s.add_argument("--label"); s.set_defaults(f=cmd_new_key)
    s = sub.add_parser("revoke-key", help="revoke key(s) by prefix"); s.add_argument("--prefix", required=True)
    s.set_defaults(f=cmd_revoke)
    sub.add_parser("list", help="list customers").set_defaults(f=cmd_list)
    s = sub.add_parser("usage", help="usage this month"); s.add_argument("--email"); s.set_defaults(f=cmd_usage)
    a = p.parse_args()
    db.init_schema()
    a.f(a)
    db.close()


if __name__ == "__main__":
    main()
