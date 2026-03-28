---
name: run
description: Start the Flask development server
user-invocable: true
allowed-tools:
  - Bash
---

# Run the App

Start the Flask development server for mail.tm.

## Steps

1. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Check that `.env` exists (warn if missing)
3. Start the server:
   ```bash
   python app.py
   ```

The app will be available at http://localhost:8000.
