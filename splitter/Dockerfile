FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY splitter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY splitter/ .
COPY shared ./shared

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000
# Optional: Add a healthcheck (if you want Docker-native health status)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "splitter.py"]
