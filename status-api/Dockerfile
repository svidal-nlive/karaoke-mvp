FROM python:3.11-slim

WORKDIR /app

COPY status-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY status-api/ .
COPY shared ./shared

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5001
CMD ["python", "status_api.py"]
