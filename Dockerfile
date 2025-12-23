FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY data ./data

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "invoice_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
