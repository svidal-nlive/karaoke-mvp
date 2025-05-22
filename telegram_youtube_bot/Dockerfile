# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps for yt-dlp and musicbrainzngs
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# For non-root operation (match your other services)
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

# Mount shared input/output/metadata directories
VOLUME ["/input", "/metadata/json"]

CMD ["python", "bot.py"]
