FROM python:3.11-slim

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
CMD ["python", "organizer.py"]
