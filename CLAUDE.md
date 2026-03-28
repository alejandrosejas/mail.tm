# CLAUDE.md — AI Assistant Guide for mail.tm

## Project Overview

A Flask web application for interacting with Mail.tm temporary email accounts. Provides a browser-based inbox viewer with auto-refresh, message reading, and email address clipboard copy.

## Tech Stack

- **Backend:** Python 3.8+ / Flask 3.0.2
- **Frontend:** HTML/CSS/JS with Bootstrap 5.3, jQuery 3.6, Font Awesome 6, Highlight.js 11.9 (all via CDN)
- **API:** Mail.tm REST API (`https://api.mail.tm`) with JWT authentication
- **Config:** python-dotenv for environment variables

## Project Structure

```
mail.tm/
├── app.py                    # Main Flask app — MailTM class + routes
├── fetch_mailtm_emails.py    # Standalone email fetch utility (for testing)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .claude/
│   ├── settings.json         # Project-level Claude Code config
│   ├── rules/                # Modular convention files (auto-loaded)
│   │   ├── flask-conventions.md
│   │   ├── frontend.md
│   │   ├── security.md
│   │   └── api-patterns.md
│   └── skills/
│       └── run/SKILL.md      # /run — start the dev server
├── templates/
│   ├── base.html             # Base template (navbar, CDN imports)
│   ├── index.html            # Inbox + message viewer
│   ├── login.html            # Login / registration page
│   └── error.html            # Error display page
└── static/
    └── css/
        └── style.css         # Custom styles
```

## Setup & Running

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit with real credentials
python app.py         # starts on http://localhost:8000
```

### Required Environment Variables (.env)

- `MAIL_TM_EMAIL` — Mail.tm email address
- `MAIL_TM_PASSWORD` — Mail.tm password
- `FLASK_SECRET_KEY` — Flask session secret

## Development Notes

- **No test suite** — no tests, pytest, or test config exist yet
- **No linter/formatter config** — no Black, Pylint, ESLint, or Prettier configured
- **No CI/CD** — no GitHub Actions workflows
- **No Docker** — no Dockerfile or docker-compose
- **Debug mode is on** — `app.run(debug=True)` in app.py

## Conventions

Detailed conventions are in `.claude/rules/`. Key points:

- Keep the app as a single `app.py` unless complexity requires splitting
- Frontend deps via CDN (no npm/bundler)
- Use `.env` for secrets; never commit `.env`
- Flask routes return templates for pages, JSON for AJAX
