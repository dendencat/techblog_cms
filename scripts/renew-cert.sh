#!/bin/bash

docker compose exec nginx nginx -s reload
docker compose run --rm certbot renew

docker compose exec nginx nginx -s reload
docker compose run --rm certbot renew