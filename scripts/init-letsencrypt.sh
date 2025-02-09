#!/bin/bash

# Create dummy certificates
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/dummy.key \
    -out /etc/nginx/ssl/dummy.crt \
    -subj "/CN=localhost"

# Start nginx
docker compose up -d nginx

# Wait for nginx to start
sleep 5

# Get the real certificate
docker compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email your@email.com \
    --agree-tos \
    --no-eff-email \
    -d blog.iohub.link

# Reload nginx to use the new certificate
docker compose exec nginx nginx -s reload
