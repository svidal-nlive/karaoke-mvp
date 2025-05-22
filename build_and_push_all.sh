#!/bin/bash
set -e

DOCKERHUB_USER="yourdockerhubuser"   # <-- CHANGE THIS
SERVICES="watcher metadata splitter packager organizer status-api maintenance telegram_youtube_bot"
# Add more as needed (maintenance-cron etc.)

for service in $SERVICES; do
  echo "==== Building $service ===="
  docker build -t $DOCKERHUB_USER/karaoke-$service:latest ./$service
  echo "==== Pushing $service ===="
  docker push $DOCKERHUB_USER/karaoke-$service:latest
done

echo "All images built and pushed to DockerHub!"
