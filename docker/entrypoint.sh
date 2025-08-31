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
chmod 777 /app/logs
chmod 666 /app/logs/access.log

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
    python manage.py create_test_data
fi

# -------------------------------------------
# 静的ファイルの収集
# -------------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput

# -------------------------------------------
# 静的ファイルディレクトリの作成と権限設定
# -------------------------------------------
echo "Setting permissions for static files..."
mkdir -p /app/static
chmod -R 755 /app/static
chown -R appuser:appgroup /app/static

# -------------------------------------------
# Gunicorn の起動（標準出力にログを出力）
# -------------------------------------------
echo "Starting Gunicorn..."
exec gunicorn techblog_cms.wsgi:application \
    --bind 0.0.0.0:8000 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --workers 3
