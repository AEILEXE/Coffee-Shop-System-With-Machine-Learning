
# CaféCraft Coffee Shop System

## Overview
This is a Point-of-Sale (POS) and Inventory Management System for a coffee shop, featuring user authentication, reporting, and a machine learning-based recommender. The system is modular and uses a local SQLite database.

## Setup Instructions

1. **Install Python 3.10+** (if not already installed).
2. (Recommended) Create a virtual environment:
	```sh
	python -m venv venv
	venv\Scripts\activate  # On Windows
	```
3. **Install dependencies:**
	```sh
	pip install -r requirements.txt
	```
4. **Run the auto-setup script:**
	```sh
	python auto_setup.py
	```
	This will check/install packages, set up the database, and verify assets.
5. **Start the application:**
	```sh
	python main.py
	```

## Notes & Recommendations
- Default database: `cafecraft.db` (auto-created if missing)
- To reset or repair the system, re-run `python auto_setup.py`
- User roles: Owner (full access), Employee (POS only)
- For integration testing, use `python test_integration.py`
- All modules are in their respective folders (auth, inventory, pos, reports, etc.)
- For custom settings, see `config/settings.py`

## Project Structure
- `main.py` — Main entry point (GUI)
- `auto_setup.py` — Automated setup/repair
- `requirements.txt` — Python dependencies
- `test_integration.py` — Integration test script
- `auth/`, `inventory/`, `pos/`, `reports/`, `ml/`, `ui/`, `utils/` — Core modules

---
For more details, see comments in each module or contact the maintainer.