# Running the business: operations guide

Commands run on the server in `/opt/invoiceformat` (locally: in the project folder).
For production, prefix compose commands with the two files:

```bash
alias dc='docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml'
```

## Customers and keys (admin command line)
| Task | Command |
|---|---|
| List customers | `dc exec api python -m app.admin list` |
| New paying customer | `dc exec api python -m app.admin create --email buyer@company.com --name "Company" --plan starter` |
| Upgrade / downgrade | `dc exec api python -m app.admin set-plan --email buyer@company.com --plan growth` |
| Cancelled subscription | `dc exec api python -m app.admin set-plan --email buyer@company.com --plan free` |
| Lost key → new key | `dc exec api python -m app.admin new-key --email buyer@company.com` |
| Leaked key → revoke | `dc exec api python -m app.admin revoke-key --prefix ifk_live_AbCd` (prefix from `list`) |
| Usage this month | `dc exec api python -m app.admin usage` |

RapidAPI marketplace customers are created automatically on their first call, as `rapidapi:<their RapidAPI username>` on the internal `rapidapi` plan. RapidAPI bills them and enforces their quota; `usage` shows their activity.

Plans and prices live in `service/app/plans.py` (rebuild and restart after changing).
API keys are shown only once. Send them to customers through a private channel, never in a public ticket.

## The sales routine (manual billing, version 1)
1. The customer pays through your payment provider's checkout link (see [SELLING.md](SELLING.md)).
2. You receive the payment notification email.
3. Run `set-plan` (existing free user) or `create` (new customer) with their email.
4. Reply with a short welcome: their plan, quota, the docs link (`/docs`) and how to reach you.
5. On cancellation or failed payment: `set-plan ... --plan free`.

This is deliberately manual. Automate it with the provider's webhooks once you have about 10 paying customers.

## Health and logs
| Check | Command |
|---|---|
| Are all services healthy? | `dc ps` |
| Service health | `curl https://api.yourdomain.com/v1/health` |
| Live API log | `dc logs -f api` |
| Errors only | `dc logs api 2>&1 \| grep -iE 'error\|exception'` |

Each API log line is JSON with a request id, path, status, duration and customer id. It never contains invoice data or keys. When a customer reports a problem, ask for the `X-Request-ID` header value and search for it: `dc logs api | grep <id>`.

## Backups and restore
- Daily backups: `deploy/backup.sh` (set up as a cron job in DEPLOY.md). It keeps 14 days.
- Restore (overwrites the current data):

```bash
gunzip -c backups/invoiceformat-YYYYmmdd-HHMMSS.sql.gz | dc exec -T db psql -U app -d invoiceformat
```

- Practise a restore every few months (tested on 2026-11-09: 34 customers, 34 keys and 962 usage rows restored identically).

## If something breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `/v1/health` says `validator: down` | Validator container crashed | `dc restart validator`; check `dc logs validator` |
| `database: down` | DB stopped / disk full | `dc ps`, `df -h`; free disk space; `dc up -d db` |
| `cache: down` | Redis stopped | `dc up -d redis`. The API keeps working, but rate limits are not enforced meanwhile |
| Website shows certificate error | DNS not pointing at server, or ports 80/443 blocked | Check the DNS A record and the firewall (`ufw status`) |
| Everything slow | CPU maxed by PDF generation | `docker stats`; move to a bigger server or raise uvicorn workers in `service/Dockerfile` |

## Security routine
- Update the server monthly (`apt update && apt upgrade`), and the Docker images when new versions of the pinned base images are released.
- Keep `.env` private (it holds the database password). It is ignored by git.
- Never expose the validator, database or Redis ports. Only Caddy (80/443) is public.
- Rotate a customer's key immediately if they report a leak (`new-key`, then `revoke-key`).

## Scaling later (not needed at launch)
- More throughput: increase `--workers` in `service/Dockerfile` (about 1 per CPU core) and the server size.
- Large batch customers: add a job queue (generation takes ~0.1–0.7 s per invoice).
- Automate billing with payment-provider webhooks; add monthly invoices for usage.
