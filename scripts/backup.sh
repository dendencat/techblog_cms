#!/bin/bash
# DB とアップロード画像を日付付きでバックアップする(自宅マシン運用向け)。
#   ./scripts/backup.sh                 # ./backups に保存、14 日より古いものは削除
#   BACKUP_DIR=/mnt/usb/techblog KEEP_DAYS=30 ./scripts/backup.sh
# cron 例(毎日 3:30): 30 3 * * * /path/to/techblog_cms/scripts/backup.sh >> /var/log/techblog-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR=${BACKUP_DIR:-./backups}
KEEP_DAYS=${KEEP_DAYS:-14}
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml)
STAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
umask 077

echo "[$(date -Is)] Dumping database..."
"${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner' \
    | gzip > "$BACKUP_DIR/db_${STAMP}.sql.gz"

echo "[$(date -Is)] Archiving media..."
"${COMPOSE[@]}" exec -T django tar -C /app/media -czf - . > "$BACKUP_DIR/media_${STAMP}.tar.gz"

find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db_*.sql.gz' -o -name 'media_*.tar.gz' \) \
    -mtime +"$KEEP_DAYS" -delete

echo "[$(date -Is)] Done: $BACKUP_DIR (db_${STAMP}.sql.gz, media_${STAMP}.tar.gz)"
