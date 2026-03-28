# Mail.tm API Patterns

- Base URL: `https://api.mail.tm`
- Authentication: JWT bearer token via `POST /token`
- All authenticated requests use `Authorization: Bearer <token>` header
- Pagination: use `page` query parameter; response uses `hydra:member` for results
- PATCH requests require `Content-Type: merge-patch+json`
- Handle 401 responses by clearing the session and redirecting to login
