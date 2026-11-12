#!/bin/bash
# Usage: ./restore.sh backups/backup_20241030_020000.sql.gz
set -e
FILE="$1"
if [ -z "$FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi
echo "[restore] dropping and recreating database..."
docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS forwarder;"
docker compose exec -T db psql -U postgres -c "CREATE DATABASE forwarder;"
echo "[restore] loading $FILE ..."
gunzip -c "$FILE" | docker compose exec -T db psql -U postgres forwarder
echo "[restore] done."
