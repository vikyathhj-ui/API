#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Database backup: customers, API key hashes, usage. (Invoice contents are never stored.)
#   bash deploy/backup.sh            -> backups/invoiceformat-YYYYmmdd-HHMMSS.sql.gz
# Keeps the newest 14 backups. Run daily with cron, e.g.:
#   17 3 * * * cd /opt/invoiceformat && bash deploy/backup.sh >> backups/backup.log 2>&1
# Copy backups OFF the server too (another machine or storage box): a backup on the
# same disk does not survive the server being lost.
#
# Restore (overwrites current data!):
#   gunzip -c backups/FILE.sql.gz | docker compose exec -T db psql -U app -d invoiceformat
# -----------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
file="backups/invoiceformat-$(date -u +%Y%m%d-%H%M%S).sql.gz"
docker compose exec -T db pg_dump -U app -d invoiceformat --clean --if-exists | gzip > "$file"
[[ -s "$file" ]] || { echo "backup failed: empty file"; rm -f "$file"; exit 1; }
ls -1t backups/invoiceformat-*.sql.gz | tail -n +15 | xargs -r rm --
echo "backup ok: $file ($(du -h "$file" | cut -f1))"
