FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

COPY maintenance/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY maintenance/ .
COPY shared ./shared

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

# (You can add a HEALTHCHECK here if/when this container exposes an API.)

CMD ["python", "cleanup.py"]
