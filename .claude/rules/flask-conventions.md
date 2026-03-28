# Flask Conventions

- Keep the app as a single `app.py` file unless complexity requires splitting
- Use the `create_app()` application factory pattern
- Flask routes return rendered templates for page loads, JSON for AJAX endpoints
- Error handling uses try/except with `error.html` template fallback
- CORS is enabled via flask-cors
- Use `session` for storing auth tokens; never expose tokens in URLs or logs
- The `MailTM` class wraps all Mail.tm API calls; do not make raw `requests` calls outside it
