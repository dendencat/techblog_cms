#!/bin/bash

# Exit on any error
set -e

# Navigate to the project directory
cd "$(dirname "$0")"

# Pull the latest changes from the repository
echo "Pulling latest changes..."
git pull origin main || {
    echo "Failed to pull latest changes"
    exit 1
}

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
docker compose down || {
    echo "Failed to stop containers"
    exit 1
}

# Build the Docker images
echo "Building Docker images..."
docker compose build --no-cache || {
    echo "Failed to build images"
    exit 1
}

# Start the containers
echo "Starting the containers..."
docker compose up -d || {
    echo "Failed to start containers"
    exit 1
}

echo "Deployment completed!"
