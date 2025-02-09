#!/bin/bash

set -e

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# ディレクトリ作成
mkdir -p "./nginx/ssl"
chmod 755 "./nginx/ssl"

echo "Creating dummy certificate..."
openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE \
    -days 1 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:$DOMAIN"

chmod 644 "./nginx/ssl/privkey.pem" "./nginx/ssl/fullchain.pem"

echo "Starting nginx..."
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 10

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

echo "Copying Let's Encrypt certificates..."
docker compose run --rm --entrypoint "\
    cp -L /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/nginx/ssl/ && \
    cp -L /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/nginx/ssl/ && \
    chmod 644 /etc/nginx/ssl/privkey.pem /etc/nginx/ssl/fullchain.pem" certbot

echo "Restarting nginx..."
docker compose restart nginx

echo "Initialization completed successfully"
