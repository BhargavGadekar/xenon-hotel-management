#!/usr/bin/env python3
"""
XENON · Palace & Residences
Universal Cross-Platform Runner (Linux, macOS, Windows)

Usage:
    python run.py
    python3 run.py
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

# Resolve absolute paths cross-platform
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
STATIC_DIR = ROOT_DIR / "static"

# Ensure backend directory is in python search path
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def print_banner():
    print("=" * 66)
    print("      X E N O N  ·  P A L A C E  &  R E S I D E N C E S")
    print("          Hotel & Lodge Management POS Terminal")
    print("=" * 66)
    print(f"Platform: {sys.platform} (OS-Agnostic Engine)")
    print(f"Working Directory: {ROOT_DIR}")
    print("")

def check_dependencies():
    """Verify required python packages are installed."""
    required = ["fastapi", "uvicorn", "pydantic"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installing missing requirements ({', '.join(missing)})...")
        req_file = BACKEND_DIR / "requirements.txt"
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("Failed to install dependencies automatically. Please run:")
            print(f"    {sys.executable} -m pip install -r backend/requirements.txt")
            sys.exit(1)
        print("✓ Dependencies verified.")
    else:
        print("✓ Dependencies verified.")

def init_database():
    """Ensure SQLite database and starter seeds exist."""
    try:
        import database
        database.init_db()
        print("✓ Hotel database & starter suites initialized.")
    except Exception as e:
        print(f"Database initialization warning: {e}")

def main():
    print_banner()
    check_dependencies()
    init_database()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    url = f"http://{host}:{port}"

    print("")
    print(f"Starting server at: {url}")
    print("Press Ctrl+C to terminate.")
    print("-" * 66)

    # Automatically launch default browser in background after short delay
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch uvicorn
    import uvicorn
    uvicorn.run("app:app", host=host, port=port, reload=True, app_dir=str(BACKEND_DIR))

if __name__ == "__main__":
    main()
