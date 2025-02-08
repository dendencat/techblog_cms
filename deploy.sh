#!/bin/bash# Check for changesecho "Checking for changes..."if ! git diff --quiet HEAD; then  # Pull the latest changes from the repository  echo "Pulling latest changes..."  git pull origin main  # Stop and remove existing containers  echo "Stopping and removing existing containers..."  docker compose down  # Build the Docker images  echo "Building Docker images..."  docker compose build --no-cache  # Start the containers  echo "Starting the containers..."  docker compose up -d

  echo "Deployment completed!"
else
  echo "No changes detected. Skipping deployment."
fi#!/bin/bash

# Pull the latest changes from the repository
echo "Pulling latest changes..."
git pull origin main

# Stop and remove existing containers
echo "Stopping and removing existing containers..."
docker compose down

# Build the Docker images
echo "Building Docker images..."
docker compose build --no-cache

# Start the containers
echo "Starting the containers..."
docker compose up -d

echo "Deployment completed!"