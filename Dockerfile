FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Install the app package
RUN pip install -e .

# Expose port
EXPOSE 8080

# Start the FastAPI server
CMD sh -c "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"