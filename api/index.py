"""
Vercel serverless entry point for Django (parfumoray).

Vercel Python runtime requires this file at the `api/` level.
It adds the project root to sys.path and exposes the WSGI application.
"""

import os
import sys
from pathlib import Path

# Project root = one level up from api/
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parfumoray.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
