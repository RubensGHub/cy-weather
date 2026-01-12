# Use an official Python runtime as a parent image
FROM python:3.10-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better layer caching)
COPY pyproject.toml ./

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install the project's dependencies only (not the project itself yet)
RUN pip install --no-cache-dir .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project source code
COPY . /app

# Install the project itself in production mode
RUN pip install --no-cache-dir --no-deps .

# Expose port (optional, for documentation)
EXPOSE 8000

# Run the FastAPI application
# Uses `--host 0.0.0.0` to allow access from outside the container
CMD ["fastapi", "run", "--host", "0.0.0.0"]