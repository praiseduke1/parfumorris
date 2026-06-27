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

# Declare app at module level so Vercel's static analyzer can find it
application = None
_startup_error = None

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception:
    _startup_error = traceback.format_exc()
    print("FATAL: Django WSGI startup failed:", file=sys.stderr)
    print(_startup_error, file=sys.stderr)


def app(environ, start_response):
    """Top-level WSGI callable required by Vercel."""
    if application is not None:
        return application(environ, start_response)
    # Django failed to start — return the traceback as plain text
    body = f"Django startup error:\n\n{_startup_error}".encode("utf-8")
    start_response("500 Internal Server Error", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(body))),
    ])
    return [body]
