"""
Vercel serverless entry point for Django (parfumoray).

Vercel Python runtime requires this file at the `api/` level.
It adds the project root to sys.path and exposes the WSGI application.
"""

import os
import sys
import traceback
from pathlib import Path

# Project root = one level up from api/
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parfumoray.settings')

try:
    from django.core.wsgi import get_wsgi_application  # noqa: E402
    app = get_wsgi_application()
except Exception as e:
    error_trace = traceback.format_exc()
    print("FATAL: Django WSGI startup failed:", file=sys.stderr)
    print(error_trace, file=sys.stderr)

    # Return a plain HTTP 500 that shows the traceback in Vercel logs
    def app(environ, start_response):
        body = f"Django startup error:\n\n{error_trace}".encode("utf-8")
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
