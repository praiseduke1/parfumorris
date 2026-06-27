#!/bin/bash
# Build script for Vercel deployment

echo "=== Starting build ==="

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear || echo "collectstatic failed or skipped"

# Run database migrations
echo "=== Running database migrations ==="
python manage.py migrate --noinput || echo "Database migrations failed or skipped"

echo "=== Build complete ==="
