# Base image
FROM python:3.12-slim

# Set environment variables (prevents .pyc files and buffered outputs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy and Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create static files directory
RUN mkdir -p /app/staticfiles

# Run Django server using Gunicorn (Production-ready)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
