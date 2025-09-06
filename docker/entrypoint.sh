#!/bin/bash
set -e

# ログファイルの設定
if [ ! -f /app/logs/access.log ]; then
    touch /app/logs/access.log
fi
if [ ! -f /app/logs/error.log ]; then
    touch /app/logs/error.log
fi

# ログディレクトリの権限設定
echo "Setting up log directory..."
mkdir -p /app/logs
chown -R appuser:appgroup /app/logs
chmod 755 /app/logs || true
chmod 664 /app/logs/access.log || true

# 静的ファイルディレクトリの作成と権限設定（collectstatic 前に実施）
echo "Preparing static directory..."
mkdir -p /app/static
chown -R appuser:appgroup /app/static
chmod -R 755 /app/static || true

# -------------------------------------------
# データベースの起動待機
# -------------------------------------------
echo "Waiting for database..."
while ! nc -z db 5432; do
  echo "Waiting for database..."
  sleep 1
done
echo "Database is available!"

# -------------------------------------------
# データベースマイグレーションの実行
# -------------------------------------------
echo "Creating migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

# -------------------------------------------
# 開発環境の場合はマイグレーションファイルの作成とテストデータの作成
# -------------------------------------------
if [ "$DJANGO_ENV" = "development" ]; then
    echo "Creating test data..."
    python manage.py create_test_data || true
fi

# -------------------------------------------
# 静的ファイルの収集
# -------------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput

# -------------------------------------------
# 静的ファイルディレクトリの作成と権限設定
# -------------------------------------------
echo "Verifying static permissions..."
chown -R appuser:appgroup /app/static || true
chmod -R 755 /app/static || true

# -------------------------------------------
# Gunicorn の起動（appuserとして実行）
# -------------------------------------------
echo "Starting Gunicorn as appuser..."
exec gunicorn --config gunicorn.conf.py techblog_cms.wsgi:application
