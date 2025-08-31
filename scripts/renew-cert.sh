#!/bin/bash

set -e  # エラー発生時に終了

LOG_FILE="/var/log/certbot/renewal.log"

# ログディレクトリの作成
sudo mkdir -p "$(dirname $LOG_FILE)"

# 証明書の更新
if docker compose run --rm certbot renew --quiet >> "$LOG_FILE" 2>&1; then
    # Nginx設定の再読み込み
    docker compose exec nginx nginx -s reload
    echo "Certificate renewed successfully"
else
    echo "Certificate renewal failed. Check $LOG_FILE for details"
    exit 1
fi