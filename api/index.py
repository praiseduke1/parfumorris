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

_startup_error = None

try:
    from django.core.wsgi import get_wsgi_application
    from django.core.management import call_command
    from django.db import connection

    application = get_wsgi_application()

    _db_initialized = False

    def _ensure_data():
        global _db_initialized
        if _db_initialized:
            return

        try:
            cur = connection.cursor()
            cur.execute("SELECT COUNT(*) FROM products_product")
            count = cur.fetchone()[0]

            if count == 0:
                print("Cold start: DB empty — restoring reference data...", flush=True)
                ref_path = os.path.join(os.path.dirname(__file__), "reference_data.json")
                if os.path.exists(ref_path):
                    call_command("loaddata", ref_path, verbosity=0)
                    print("Cold start: reference data loaded.", flush=True)
                else:
                    print(f"Cold start: {ref_path} not found, skipping.", flush=True)

                print("Cold start: running placeholder generation...", flush=True)
                try:
                    call_command("generate_placeholders")
                except Exception as e:
                    print(f"Cold start: placeholders skipped ({e})", flush=True)
            else:
                print(f"Cold start: DB has {count} products, skipping restore.", flush=True)
        except Exception as e:
            print(f"Cold start: init error (non-fatal): {e}", flush=True)
            return

        _db_initialized = True

except Exception:
    _startup_error = traceback.format_exc()
    print("FATAL: Django WSGI startup failed:", file=sys.stderr)
    print(_startup_error, file=sys.stderr)
    _db_initialized = True


def app(environ, start_response):
    """Top-level WSGI callable required by Vercel."""
    if application is not None:
        _ensure_data()
        return application(environ, start_response)
    body = f"Django startup error:\n\n{_startup_error}".encode("utf-8")
    start_response("500 Internal Server Error", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(body))),
    ])
    return [body]
