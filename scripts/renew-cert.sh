#!/bin/bash

# Renew the certificate
docker compose run --rm certbot renew --quiet

# Check if renewal was successful
if [ $? -eq 0 ]; then
    # Reload nginx configuration
    docker compose exec nginx nginx -s reload
    echo "Certificate renewed successfully"
else
    echo "Certificate renewal failed"
    exit 1
fi