#!/bin/bash

DOMAIN="blog.iohub.link"
EMAIL="your@email.com"
RSA_KEY_SIZE=4096

# Create required directories with sudo
sudo mkdir -p "./nginx/ssl"
sudo chown -R $USER:$USER "./nginx/ssl"
sudo chmod -R 755 "./nginx/ssl"

# Generate dummy certificates first
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "./nginx/ssl/privkey.pem" \
    -out "./nginx/ssl/fullchain.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost"

sudo chmod 644 "./nginx/ssl/privkey.pem" "./nginx/ssl/fullchain.pem"

# Stop any running containers
docker compose down

# Start nginx with dummy certificates
docker compose up -d nginx
echo "Waiting for nginx to start..."
sleep 10

# Request Let's Encrypt certificate
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --staging \
    --force-renewal \
    -d $DOMAIN

# Ensure proper permissions
sudo chown -R $USER:$USER "./nginx/ssl"
sudo chmod -R 755 "./nginx/ssl"
sudo chmod 644 "./nginx/ssl/fullchain.pem" "./nginx/ssl/privkey.pem"

# Restart nginx to load the new certificate
docker compose restart nginx

echo "Initialization completed"
