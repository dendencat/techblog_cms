#!/bin/bash

set -e

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# クリーンアップ
echo "Cleaning up old certificates..."
rm -rf "./nginx/ssl/"*
mkdir -p "./nginx/ssl"
chmod 755 "./nginx/ssl"

echo "Creating dummy certificate..."
openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE \
    -days 1 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN" \
    -addext "basicConstraints=CA:FALSE" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

chmod 644 "./nginx/ssl/"*.pem

# 既存のコンテナを停止
docker compose down

echo "Starting nginx..."
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 10

echo "Requesting Let's Encrypt certificate..."
docker compose run --rm --entrypoint "\
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN" certbot

echo "Copying certificates..."
docker compose run --rm --entrypoint "\
    sh -c 'cp -f /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/nginx/ssl/ && \
    cp -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/nginx/ssl/ && \
    chmod 644 /etc/nginx/ssl/*.pem'" certbot

echo "Restarting services..."
docker compose up -d

echo "Initialization completed successfully"
