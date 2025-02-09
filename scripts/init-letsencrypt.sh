#!/bin/bash

set -e  # エラー発生時に終了

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# 関数定義
check_requirements() {
    if ! command -v docker compose >/dev/null 2>&1; then
        echo "Error: docker compose is not installed"
        exit 1
    fi
}

# 要件チェック
check_requirements

# Create required directories with sudo
sudo mkdir -p "./nginx/ssl"
sudo chown -R $USER:$USER "./nginx/ssl"
sudo chmod -R 755 "./nginx/ssl"

# Generate dummy certificates first
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:blog.iohub.link"

sudo chmod 644 "./nginx/ssl/privkey.pem" "./nginx/ssl/fullchain.pem"

# Stop any running containers
docker compose down

# Start nginx with dummy certificates
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 10

# Request Let's Encrypt certificate
if ! docker compose run --rm --entrypoint "\
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --staging \
    -d $DOMAIN" certbot; then
    echo "Error: Failed to obtain certificate"
    exit 1
fi

# Start all services
docker compose up -d

echo "Initialization completed successfully"
