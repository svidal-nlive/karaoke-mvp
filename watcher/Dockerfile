# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Set workdir and environment
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install ffmpeg (required for audio file handling)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Mount shared pipeline_utils.py at /app/shared via docker-compose (do NOT COPY here)

# Create and use non-root user
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose Flask port
EXPOSE 5000

# Mount input and queue directories as volumes
VOLUME ["/input", "/queue"]

# Entry point
CMD ["python", "watcher.py"]
