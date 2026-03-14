FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the app package
RUN pip install -e .

# Expose port
EXPOSE 8080

# Start the FastAPI server
CMD sh -c "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"