"""
auto_setup.py

A reusable bootstrapper module that checks and installs required Python
packages, verifies and downloads assets, initializes or repairs a sqlite3
database, and provides console (and optional simple GUI) feedback.

Usage as module:
    from auto_setup import setup_system
    setup_system(run_gui=False, verbose=True, retries=2)

Usage from CLI:
    python auto_setup.py                 # Run setup with console feedback
    python auto_setup.py --gui           # Run with Tkinter progress window
    python auto_setup.py --verbose       # Detailed output
    python auto_setup.py --retries 3     # Custom retry count
    python auto_setup.py --no-db         # Skip database checks

The module is idempotent: safe to run multiple times. It attempts retries
for transient issues and logs progress to the console. Customize
`REQUIRED_PACKAGES`, `ASSETS`, and `DEFAULT_DB_SCHEMA` as needed.
"""

import os
import sys
import subprocess
import sqlite3
import time
import shutil
import hashlib
import importlib
import argparse
from typing import Dict, Optional

RETRY_DELAY = 2

# Packages your app needs. Version specifiers are allowed (e.g. 'requests>=2.28').
# Update this list to match your project's actual third-party dependencies.
REQUIRED_PACKAGES = [
    "requests>=2.0",
    "customtkinter>=5.2",
    "matplotlib>=3.0",
    "bcrypt>=3.0",
    "pandas>=1.0",
    "scikit-learn>=1.0",
    "numpy>=1.20",
    "reportlab>=3.0",
]

# Assets to verify: mapping of local path -> download URL
# Customize this dictionary per project needs. Leave empty to skip downloads.
ASSETS: Dict[str, str] = {
}

# Default sqlite DB location and a tiny default schema to support login repair.
# Prefer using the project's configured DB path when available.
try:
    # database.__init__ exports DB_PATH
    from database import DB_PATH as PROJECT_DB_PATH
    DEFAULT_DB_PATH = PROJECT_DB_PATH
except Exception:
    DEFAULT_DB_PATH = os.path.join("database", "app.db")
DEFAULT_DB_SCHEMA = """
-- Users table used for simple login repairs
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class ProgressReporter:
    """Simple progress reporter that prints updates and optionally shows a small Tkinter window."""

    def __init__(self, use_gui: bool = False):
        self.use_gui = use_gui
        self.messages = []
        self.gui = None
        if self.use_gui:
            try:
                import tkinter as tk

                self.tk = tk
                self.root = tk.Tk()
                self.root.title("Setup Progress")
                self.label = tk.Label(self.root, text="Starting setup...", justify=tk.LEFT)
                self.label.pack(padx=10, pady=10)
                # Run the GUI in non-blocking mode by updating in the background
                self.root.update()
            except Exception:
                # If Tk isn't available or fails, fall back to console only
                self.use_gui = False

    def info(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        text = f"[{timestamp}] {msg}"
        self.messages.append(text)
        print(text)
        if self.use_gui:
            try:
                self.label.config(text="\n".join(self.messages[-10:]))
                self.root.update()
            except Exception:
                self.use_gui = False

    def close(self):
        if self.use_gui:
            try:
                self.root.destroy()
            except Exception:
                pass


def _run_pip_install(pkg: str, reporter: ProgressReporter) -> bool:
    """Install a package using pip via subprocess. Returns True on success."""
    reporter.info(f"Installing package: {pkg}")
    try:
        cmd = [sys.executable, "-m", "pip", "install", pkg]
        subprocess.check_call(cmd)
        reporter.info(f"Successfully installed: {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        reporter.info(f"pip install failed for {pkg}: {e}")
        return False


def check_and_install_packages(packages, reporter: ProgressReporter, retries: int = 2):
    """Ensure each package can be imported, otherwise install it.

    packages: list of package specifiers (pip style)
    """
    # Ensure `pip` will be usable; attempt to upgrade pip first (best-effort)
    try:
        reporter.info("Attempting to upgrade pip (best-effort)")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception:
        reporter.info("pip upgrade failed or not necessary; continuing")

    for pkg in packages:
        # Derive an importable module name from package spec (simple heuristic)
        module_name = pkg.split("==")[0].split(">=")[0].split("<")[0].split("[")[0]
        module_name = module_name.strip()
        success = False
        for attempt in range(retries + 1):
            try:
                importlib.import_module(module_name)
                reporter.info(f"Package available: {module_name}")
                success = True
                break
            except Exception:
                reporter.info(f"Package {module_name} not importable; attempt {attempt + 1}")
                installed = _run_pip_install(pkg, reporter)
                if not installed:
                    time.sleep(RETRY_DELAY)
                    continue
        if not success:
            reporter.info(f"Warning: Unable to ensure package: {pkg}")


def download_file(url: str, dest_path: str, reporter: ProgressReporter, retries: int = 2) -> bool:
    """Download a file from url to dest_path. Returns True if successful."""
    try:
        import requests
    except Exception:
        reporter.info("`requests` not available when trying to download; attempting to install it.")
        if not _run_pip_install("requests", reporter):
            reporter.info("Cannot download asset because requests installation failed.")
            return False
        import requests

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)

    for attempt in range(retries + 1):
        try:
            reporter.info(f"Downloading {url} -> {dest_path} (attempt {attempt + 1})")
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                tmp = dest_path + ".part"
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                os.replace(tmp, dest_path)
            reporter.info(f"Downloaded: {dest_path}")
            return True
        except Exception as e:
            reporter.info(f"Download failed: {e}")
            time.sleep(RETRY_DELAY)
    reporter.info(f"Failed to download {url} after retries")
    return False


def verify_assets(assets: Dict[str, str], reporter: ProgressReporter, retries: int = 2):
    """Verify local assets; download missing ones from provided URLs."""
    for path, url in assets.items():
        if os.path.exists(path):
            reporter.info(f"Asset present: {path}")
            continue
        reporter.info(f"Asset missing: {path}; will download from {url}")
        ok = download_file(url, path, reporter, retries=retries)
        if not ok:
            reporter.info(f"Warning: Could not obtain asset: {path}")


def import_project_schema(reporter: ProgressReporter) -> Optional[str]:
    """Try to import `database.schema` from project to get a schema SQL string."""
    try:
        spec = importlib.import_module("database.schema")
        # Try several common names
        if hasattr(spec, "SCHEMA_SQL"):
            reporter.info("Loaded SCHEMA_SQL from database.schema")
            return getattr(spec, "SCHEMA_SQL")
        if hasattr(spec, "get_schema"):
            reporter.info("Loaded schema via database.schema.get_schema()")
            return spec.get_schema()
    except Exception:
        reporter.info("No project schema found in database.schema; using default schema")
    return None


def init_or_repair_database(db_path: str, reporter: ProgressReporter, retries: int = 2):
    """Ensure sqlite DB exists with required tables; repair if corrupted."""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    schema_sql = import_project_schema(reporter) or DEFAULT_DB_SCHEMA

    for attempt in range(retries + 1):
        try:
            reporter.info(f"Initializing/repairing database at {db_path}")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.executescript(schema_sql)
            conn.commit()
            conn.close()
            reporter.info("Database initialized/verified")
            # Post-check: ensure users table exists
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if not cur.fetchone():
                    reporter.info("Users table missing; re-applying schema")
                    conn.close()
                    raise sqlite3.DatabaseError("users table missing")
                conn.close()
            except Exception:
                reporter.info("Detected missing critical tables; retrying schema application")
                time.sleep(RETRY_DELAY)
                continue
            return True
        except sqlite3.DatabaseError as e:
            reporter.info(f"SQLite error: {e}; attempting to recreate DB")
            try:
                # Try to backup corrupted DB then recreate
                if os.path.exists(db_path):
                    bak = db_path + ".bak"
                    reporter.info(f"Backing up DB to {bak}")
                    shutil.copy2(db_path, bak)
                    os.remove(db_path)
            except Exception as ex:
                reporter.info(f"Failed to backup/delete corrupted DB: {ex}")
            time.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            reporter.info(f"Unexpected DB initialization error: {e}")
            time.sleep(RETRY_DELAY)
    reporter.info("Failed to initialize/repair database after retries")
    return False


def ensure_default_admin(db_path: str, reporter: ProgressReporter, username: str = "admin", password: str = "admin"):
    """Ensure a default admin user exists in the users table.
    Passwords are stored as SHA256(password) here for simplicity; adapt to your hashed scheme.
    """
    try:
        reporter.info("Ensuring default admin user exists")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM users")
        cnt = cur.fetchone()[0]
        if cnt == 0:
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            cur.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)", (username, pw_hash))
            conn.commit()
            reporter.info(f"Created default admin user `{username}`")
        conn.close()
    except Exception as e:
        reporter.info(f"Failed to ensure default admin: {e}")


def check_environment(reporter: ProgressReporter):
    """Check simple environment requirements like write permissions and PATH entries."""
    reporter.info("Checking environment permissions")
    try:
        testfile = os.path.join(os.getcwd(), ".setup_write_test")
        with open(testfile, "w") as f:
            f.write("ok")
        os.remove(testfile)
        reporter.info("Write permission: OK")
    except Exception as e:
        reporter.info(f"Write permission check failed: {e}")

    reporter.info("Checking Python executable path")
    reporter.info(f"Python: {sys.executable}")


def repair_login_issues(db_path: str, reporter: ProgressReporter):
    """Attempt common login-related repairs (ensure users table and default user)."""
    reporter.info("Attempting to repair login issues")
    ok = init_or_repair_database(db_path, reporter)
    if ok:
        ensure_default_admin(db_path, reporter)


def setup_system(run_gui: bool = False, verbose: bool = True, retries: int = 2):
    """Main entry point to perform all checks, installs, downloads, and repairs.

    Parameters
    - run_gui: show a tiny Tkinter status window (best-effort)
    - verbose: print console messages
    - retries: how many retries for operations
    """
    reporter = ProgressReporter(use_gui=run_gui)
    reporter.info("Starting system setup...")

    # 1) Packages
    reporter.info("Checking required Python packages")
    check_and_install_packages(REQUIRED_PACKAGES, reporter, retries=retries)

    # 2) Assets
    if ASSETS:
        reporter.info("Verifying assets")
        verify_assets(ASSETS, reporter, retries=retries)
    else:
        reporter.info("No assets defined to verify")

    # 3) Database
    reporter.info("Verifying database and schema")
    db_ok = init_or_repair_database(DEFAULT_DB_PATH, reporter, retries=retries)
    if not db_ok:
        reporter.info("Database verification/repair failed")
    else:
        # Ensure default admin user exists to help login
        ensure_default_admin(DEFAULT_DB_PATH, reporter)

    # 4) Environment checks
    check_environment(reporter)

    # 5) Attempt to repair login issues automatically
    repair_login_issues(DEFAULT_DB_PATH, reporter)

    reporter.info("System setup completed. Please review messages above for any warnings.")
    reporter.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CaféCraft Auto-Setup: Check dependencies, download assets, initialize database."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Show Tkinter progress window (best-effort; falls back to console if unavailable)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print detailed progress messages (default: True)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Number of retries for failed operations (default: 2)"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip database initialization and repair"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("CaféCraft Auto-Setup & Self-Healing Bootstrapper")
    print("="*60 + "\n")

    if args.no_db:
        print("Database initialization disabled (--no-db)\n")

    try:
        setup_system(run_gui=args.gui, verbose=args.verbose, retries=args.retries)
        print("\n" + "="*60)
        print("Setup completed successfully. Ready to launch the application.")
        print("="*60 + "\n")
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal setup error: {e}")
        sys.exit(1)
