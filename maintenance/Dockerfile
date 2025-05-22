# Use a specific Python image for reproducibility
FROM python:3.11.9-slim

WORKDIR /app

# Install cron for scheduled jobs (maintenance-cron)
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

COPY maintenance/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY maintenance/ .
COPY shared ./shared

# Create and use a non-root user for safety
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000
# Optionally, add a HEALTHCHECK if you expose an API in the future

# Default: run cleanup.py (for manual or one-shot maintenance container)
CMD ["python", "cleanup.py"]
