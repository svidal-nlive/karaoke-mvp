# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mount shared pipeline_utils.py at /app/shared via docker-compose

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

VOLUME ["/output", "/organized", "/metadata/json"]

CMD ["python", "organizer.py"]
