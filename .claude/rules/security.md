# Security Rules

- Never commit `.env` — it is gitignored
- Store secrets (email, password, Flask secret key) only in `.env`
- Do not log or print JWT tokens, passwords, or API keys
- Sanitize email HTML content before rendering to prevent XSS
- Always validate and sanitize user input on the server side
- Use `secrets` module for generating passwords and tokens, never `random`
