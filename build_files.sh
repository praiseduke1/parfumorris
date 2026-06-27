#!/bin/bash
# Build script for Vercel deployment — safe for production
# NEVER flushes the database or destroys data.

set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear || echo "collectstatic failed or skipped"

echo "=== Running database migrations ==="
python manage.py migrate --noinput || echo "Database migrations failed or skipped"

echo "=== Restoring data if tables are empty ==="
python manage.py restore_production_data || echo "Data restore command not available or skipped"

echo "=== Build complete ==="
