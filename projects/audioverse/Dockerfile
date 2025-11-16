FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Celery worker command
CMD ["celery", "-A", "audioverse", "worker", "-l", "info"]
