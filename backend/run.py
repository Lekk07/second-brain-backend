"""
run.py — Start the development server.
Run this instead of app.py for clearer error messages.

Usage:
    python run.py
"""
import sys
import os

# ── 1. Check Python version ──────────────────────────────────────────
if sys.version_info < (3, 10):
    print(f"❌  Python 3.10+ required. You have {sys.version}")
    print("    Install from https://python.org")
    sys.exit(1)

# ── 2. Check required packages ───────────────────────────────────────
REQUIRED = [
    "flask",
    "flask_sqlalchemy",
    "flask_jwt_extended",
    "flask_cors",
    "dotenv",          # python-dotenv
    "werkzeug",
]
missing = []
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print("❌  Missing packages:", ", ".join(missing))
    print("    Run:  pip install -r requirements.txt")
    sys.exit(1)

# ── 3. Check .env exists ─────────────────────────────────────────────
if not os.path.exists(".env"):
    if os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅  Created .env from .env.example")
    else:
        print("⚠️   No .env file found — using defaults")

# ── 4. Start the app ─────────────────────────────────────────────────
from app import create_app

app = create_app("development")

if __name__ == "__main__":
    print("\n✅  Second Brain backend starting...")
    print("    API:    http://localhost:5000/api/health")
    print("    Press   Ctrl+C to stop\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
