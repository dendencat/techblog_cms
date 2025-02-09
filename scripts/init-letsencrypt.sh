#!/bin/bash

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# Check if certificates already exist
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Certificates already exist, skipping initialization"
    exit 0
fi

# Create dummy certificates
mkdir -p "/etc/nginx/ssl"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "/etc/nginx/ssl/dummy.key" \
    -out "/etc/nginx/ssl/dummy.crt" \
    -subj "/CN=localhost"

# Start nginx without certbot dependency
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 5

# Request the real certificate
docker compose run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN" certbot

# Restart nginx to load the new certificate
docker compose restart nginx

# Start certbot service for automatic renewals
docker compose up -d certbot

echo "Initialization completed"
