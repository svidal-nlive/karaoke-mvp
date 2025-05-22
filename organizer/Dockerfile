FROM python:3.11.9-slim

WORKDIR /app

COPY organizer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY organizer/ .
COPY shared ./shared

RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "organizer.py"]
