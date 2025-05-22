# Use a specific Python image for reproducibility
FROM python:3.11.7-slim

WORKDIR /app

# Install ffmpeg for audio extraction
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY telegram_youtube_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code and shared utilities
COPY telegram_youtube_bot/ .
COPY shared ./shared

# Create non-root user
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000
# Optional: add healthcheck for future (bot does not expose HTTP)
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 CMD ["python", "-c", "import sys; sys.exit(0)"]

CMD ["python", "bot.py"]
