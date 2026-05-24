FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: install Playwright browsers for JS-heavy portals
# RUN playwright install chromium && playwright install-deps chromium

COPY . .

# Create directories
RUN mkdir -p data logs

# Run the scheduler
CMD ["python", "main.py", "--mode", "scheduler"]
