FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY telegram_youtube_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_youtube_bot/ .
COPY shared ./shared

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 CMD ["python", "-c", "import sys; sys.exit(0)"]

CMD ["python", "bot.py"]
