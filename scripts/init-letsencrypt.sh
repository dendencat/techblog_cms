#!/bin/bash

set -e

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096
DATA_PATH="./data/certbot"

# 関数定義
check_requirements() {
    if ! command -v docker compose >/dev/null 2>&1; then
        echo "Error: docker compose is not installed"
        exit 1
    fi
}

# 要件チェック
check_requirements

# Create required directories
mkdir -p "$DATA_PATH"
mkdir -p "./nginx/ssl"
chmod 755 "./nginx/ssl"

# Generate dummy certificate
echo "Creating dummy certificate..."
openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE \
    -days 1 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:$DOMAIN"

echo "Starting nginx..."
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 10

# Remove dummy certificate and request Let's Encrypt certificate
echo "Requesting Let's Encrypt certificate for $DOMAIN..."
docker compose run --rm --entrypoint "\
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    --server https://acme-v02.api.letsencrypt.org/directory \
    -d $DOMAIN" certbot

# Copy certificates to nginx ssl directory
echo "Copying certificates to nginx ssl directory..."
cp "$DATA_PATH/live/$DOMAIN/privkey.pem" "./nginx/ssl/"
cp "$DATA_PATH/live/$DOMAIN/fullchain.pem" "./nginx/ssl/"
chmod 644 "./nginx/ssl/privkey.pem" "./nginx/ssl/fullchain.pem"

# Restart nginx
echo "Restarting nginx..."
docker compose restart nginx

echo "Initialization completed successfully"
