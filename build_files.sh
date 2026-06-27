#!/bin/bash
# Production build script for Vercel deployment.
# NEVER flushes the database or destroys data.
# Only runs: pip install → collectstatic → migrate → start.

set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Generating placeholder images ==="
python manage.py generate_placeholders

echo "=== Restoring data (skips if data already exists) ==="
python manage.py restore_production_data

echo "=== Build complete ==="
