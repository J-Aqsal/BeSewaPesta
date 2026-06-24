# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for PostgreSQL (psycopg2) and cron
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Command to run the application (starts cron, registers jobs, and runs server)
CMD service cron start && python manage.py crontab add && python manage.py runserver 0.0.0.0:8000
