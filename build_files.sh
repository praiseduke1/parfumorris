#!/bin/bash
# Build script for Vercel deployment

echo "=== Starting build ==="

# Install dependencies
pip install -r requirements.txt

# Collect static files (will skip if DISABLE_COLLECTSTATIC=1)
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "collectstatic skipped"

echo "=== Build complete ==="
