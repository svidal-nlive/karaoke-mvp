# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cleanup.py .
COPY crontab /etc/cron.d/cleanup-cron
RUN chmod 0644 /etc/cron.d/cleanup-cron && crontab /etc/cron.d/cleanup-cron

# (Shared utils are NOT copied, they are mounted via docker-compose volumes)
# VOLUME for shared is declared at runtime

CMD ["cron", "-f"]
