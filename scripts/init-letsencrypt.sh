#!/bin/bash

set -e

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# クリーンアップと権限設定
echo "Setting up directories..."
rm -rf "./nginx/ssl/"*
mkdir -p "./nginx/ssl"
chmod 755 "./nginx/ssl"

echo "Creating initial certificates..."
openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE \
    -days 1 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN" \
    -addext "basicConstraints=critical,CA:FALSE" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

chmod 644 "./nginx/ssl/"*.pem

echo "Starting services..."
docker compose down
docker compose up -d nginx
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
    --cert-name $DOMAIN \
    -d $DOMAIN" certbot

echo "Installing certificates..."
docker compose run --rm --entrypoint "\
    sh -c 'cp -fL /etc/letsencrypt/live/$DOMAIN/* /etc/nginx/ssl/ && \
    chmod 644 /etc/nginx/ssl/*.pem'" certbot

echo "Starting all services..."
docker compose up -d

echo "Testing Nginx configuration..."
docker compose exec nginx nginx -t

echo "Reloading Nginx..."
docker compose exec nginx nginx -s reload

echo "Initialization completed successfully"
