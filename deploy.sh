#!/bin/bash
# オリジンホストでの更新デプロイ(Cloudflare Tunnel 構成)。
# 手順の全体像は docs/cloudflare-deployment.md を参照。
set -euo pipefail

cd "$(dirname "$0")"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml)

echo "Pulling latest changes..."
git pull --ff-only origin main

echo "Building images..."
"${COMPOSE[@]}" build --pull

echo "Starting containers..."
"${COMPOSE[@]}" up -d --remove-orphans

echo "Deployment completed!"
"${COMPOSE[@]}" ps
