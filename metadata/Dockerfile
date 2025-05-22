# Use a pinned Python base image for reproducibility
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements first to leverage Docker cache
COPY metadata/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code and the shared utilities into the container
COPY metadata/ .
COPY shared ./shared

# Create a non-root user for security and set ownership
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the port used by the Flask app
EXPOSE 5000

# Optional: Add a Dockerfile-level healthcheck (in addition to Compose healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Set the default command
CMD ["python", "metadata_extractor.py"]
