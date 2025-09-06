#!/bin/bash
set -euo pipefail

# This script runs only on first init of the Postgres data directory.
# It creates/updates an application user using environment variables, safely.

# Prefer dedicated app credentials if provided, else fall back to POSTGRES_* values.
APP_DB_USER_EFF="${APP_DB_USER:-${POSTGRES_USER}}"
APP_DB_PASSWORD_EFF="${APP_DB_PASSWORD:-${POSTGRES_PASSWORD}}"
APP_DB_NAME_EFF="${APP_DB_NAME:-${POSTGRES_DB}}"

# Do not echo secrets
psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v app_user="$APP_DB_USER_EFF" \
  -v app_pass="$APP_DB_PASSWORD_EFF" \
  -v app_db="$APP_DB_NAME_EFF" <<'SQL'
DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user') THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_pass');
  ELSE
    EXECUTE format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'app_user', :'app_pass');
  END IF;
END
$do$;

GRANT ALL PRIVILEGES ON DATABASE :"app_db" TO :"app_user";
-- Keep consistent with previous behavior; consider removing if not needed
ALTER ROLE :"app_user" CREATEDB;
SQL
