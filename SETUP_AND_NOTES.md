# CaféCraft Setup & Notes

## Quick Setup
1. Install Python 3.10 or newer.
2. (Optional) Create and activate a virtual environment:
   ```sh
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Run the setup script:
   ```sh
   python auto_setup.py
   ```
5. Start the app:
   ```sh
   python main.py
   ```

## Important Notes
- Database: `cafecraft.db` is created automatically.
- To reset/repair, re-run `python auto_setup.py`.
- User roles: Owner (full), Employee (POS only).
- For integration test: `python test_integration.py`.
- Modules: `auth/`, `inventory/`, `pos/`, `reports/`, `ml/`, `ui/`, `utils/`.
- Custom settings: `config/settings.py`.

---
For more, see README.md or code comments.