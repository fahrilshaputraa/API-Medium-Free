# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    HOST=0.0.0.0 \
    WORKERS=4 \
    TIMEOUT=60 \
    LOG_LEVEL=info \
    PORT=8060

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and uvicorn
RUN pip install uv uvicorn

# Copy project files (including pyproject.toml)
COPY . .

# Install Python dependencies using uv
RUN uv pip install . --system

# Create volume for database
VOLUME ["/app/instance"]

# Expose port
EXPOSE 8060

# CMD directly runs uvicorn, no need for entrypoint.sh
CMD gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS --timeout $TIMEOUT --log-level $LOG_LEVEL app:app