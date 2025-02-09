#!/bin/bash

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# Create required directories
mkdir -p "./nginx/ssl"
mkdir -p "./data/certbot/conf"
mkdir -p "./data/certbot/www"

# Create dummy certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "./nginx/ssl/dummy.key" \
    -out "./nginx/ssl/dummy.crt" \
    -subj "/CN=localhost"

# Start nginx
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 5

# Request Let's Encrypt certificate
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --staging \
    -d $DOMAIN

# Copy certificates if successful
if [ -d "./data/certbot/conf/live/$DOMAIN" ]; then
    echo "Certificates successfully obtained"
    cp "./nginx/ssl/dummy.crt" "./nginx/ssl/fullchain.pem"
    cp "./nginx/ssl/dummy.key" "./nginx/ssl/privkey.pem"
fi

# Restart nginx to load the new certificate
docker compose restart nginx

echo "Initialization completed"
