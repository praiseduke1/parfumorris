"""
Vercel serverless entry point for Django (parfumoray).

Vercel Python runtime requires this file at the `api/` level.
It adds the project root to sys.path and exposes the WSGI application.
"""

import os
import sys
import socket
import traceback
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Force IPv4-only DNS resolution.
# Vercel serverless does NOT support outbound IPv6 connections.
# Supabase's direct host (db.*.supabase.co) resolves to IPv6,
# which causes "Cannot assign requested address" psycopg2 errors.
# This monkey-patch ensures getaddrinfo always returns IPv4 results.
# ─────────────────────────────────────────────────────────────
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_only_getaddrinfo

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

    def app(environ, start_response):
        body = f"Django startup error:\n\n{error_trace}".encode("utf-8")
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
