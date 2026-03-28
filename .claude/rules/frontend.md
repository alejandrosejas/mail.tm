# Frontend Conventions

- Jinja2 templating with `base.html` block inheritance
- All frontend dependencies (Bootstrap 5.3, jQuery 3.6, Font Awesome 6, Highlight.js 11.9) are loaded via CDN — no npm or bundler
- jQuery AJAX for message loading and auto-refresh
- Use Bootstrap utility classes before writing custom CSS
- Custom styles go in `static/css/style.css`
