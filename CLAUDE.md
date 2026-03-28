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
├── requirements.txt          # Python dependencies (flask, requests, python-dotenv, flask-cors)
├── .env.example              # Environment variable template
├── templates/
│   ├── base.html             # Base template (navbar, Bootstrap/jQuery CDN imports)
│   ├── index.html            # Inbox + message viewer (extends base.html)
│   └── error.html            # Error display page
└── static/
    └── css/
        └── style.css         # Custom styles (gradients, responsive, animations)
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

## Key Code Patterns

### Backend (app.py)

- **`MailTM` class** — wraps API auth and message fetching; single instance created at module level
- **Routes:**
  - `GET /` — renders inbox (template with message list)
  - `GET /message/<message_id>` — returns message content as JSON (AJAX endpoint)
  - `GET /refresh` — returns refreshed message list as JSON (AJAX endpoint)
- Error handling uses try/except with `error.html` template fallback
- CORS enabled via flask-cors

### Frontend (templates/ + static/)

- Jinja2 templating with `base.html` block inheritance
- jQuery AJAX for message loading and 30-second auto-refresh
- Inline `onclick` handlers for message selection and clipboard copy
- Highlight.js for XML/HTML content rendering in emails

## Development Notes

- **No test suite** — no tests, pytest, or test config exist yet
- **No linter/formatter config** — no Black, Pylint, ESLint, or Prettier configured
- **No CI/CD** — no GitHub Actions workflows
- **No Docker** — no Dockerfile or docker-compose
- **Debug mode is on** — `app.run(debug=True)` in app.py

## Conventions

- Keep the app as a single `app.py` file unless complexity requires splitting
- Frontend dependencies are loaded via CDN (no npm/bundler)
- Use `.env` for secrets; never commit `.env` (it's gitignored)
- Flask routes return rendered templates for page loads, JSON for AJAX endpoints
