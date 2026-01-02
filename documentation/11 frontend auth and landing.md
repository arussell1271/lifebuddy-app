# Frontend: Landing, Auth, Dashboard (Demo)

This file documents the minimal landing, authentication, and dashboard pages added for development/demo purposes. If these files are lost, follow the steps below to rebuild.

Files added:
- `app/main.py` — Routes for landing, login, register, reset-password, dashboard.
- `app/templates/*` — Jinja2 templates: `base.html`, `landing.html`, `login.html`, `register.html`, `reset.html`, `dashboard.html`.
- `app/static/styles.css` — Minimal styling.

Key endpoints the App calls on Engine:
- `POST /api/v1/auth/register` — create account (form data: `username`, `password`).
- `POST /api/v1/auth/login` — authenticate (form data: `username`, `password`). Returns JWT in JSON.
- `GET /api/v1/me` — returns `{user_id, username, message}` when provided `Authorization: Bearer <token>`.
- `GET /api/v1/db_test` — Engine attempts a Postgres connection and reports status.

How the flow works (adhere to architecture rules):
- The App never connects directly to the DB; it proxies auth and DB-check requests to the Engine.
- On successful login the App stores the JWT in a `access_token` cookie (httponly) for the demo.

Rebuild steps (if files are lost):
1. Recreate `app/templates` and `app/static` with the filenames above. The templates are minimal Jinja2 templates extending `base.html`.
2. Implement `app/main.py` to mount static files, configure `Jinja2Templates`, and provide routes:
   - `GET /` -> `landing.html`
   - `GET /login`, `POST /login` -> calls Engine login
   - `GET /register`, `POST /register` -> calls Engine register
   - `GET /reset-password` -> placeholder
   - `GET /dashboard` -> calls Engine `/api/v1/me` (with JWT) and `/api/v1/db_test`
3. Ensure `app_requirements.txt` includes `httpx`, `jinja2`, and `fastapi` (already present).
4. Ensure Engine exposes the endpoints above (see `engine/main.py`).

Security note:
- The demo stores a JWT in a cookie for convenience only. In production follow the project's security and RLS rules and implement proper session management, secure cookies, CSRF protections, and password reset flows.

If you want, I can:
- Add CSRF protection and proper logout.
- Wire the reset password flow to a token-based flow persisted in the Engine.

*** End of doc
