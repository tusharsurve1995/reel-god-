# REEL GOD — Deployment & Security Guide

This covers running the dashboard safely anywhere: locally, on your phone/laptop,
or hosted publicly (Render/Railway) as an installable web app (PWA).

## 1. Run locally

```bash
pip install -r requirements.txt
python main.py           # or: python -m dashboard.app
```

Open http://127.0.0.1:5000. On first run (no accounts yet) you're taken to a
signup page to create the first admin. If none is created, a bootstrap
`admin / admin` account is seeded — **change its password immediately** on the
⚙️ Settings page.

## 2. Deploy publicly (Render, free tier)

1. Push to GitHub.
2. Render → **New +** → **Blueprint** → select this repo (`render.yaml` is auto-detected).
3. Add your free API keys in the **Environment** tab (`GEMINI_API_KEY`, etc.).
4. Deploy. Open the service URL and create your admin account.

The blueprint already sets a random `DASHBOARD_SECRET_KEY`, enables HTTPS-only
cookies (`SESSION_COOKIE_SECURE=1`), and uses `/healthz` for health checks.

## 3. Install as an app (PWA)

Open the site in Chrome/Safari → address-bar **Install** icon (desktop) or
**Add to Home Screen** (mobile). It then launches full-screen with its own icon.

## 4. Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `5000` | Bind port (hosting platforms inject this). |
| `DASHBOARD_SECRET_KEY` | auto-generated | Session signing key. A strong random one is generated & saved to `.env` on first run if unset. **Set explicitly in production.** |
| `SESSION_COOKIE_SECURE` | `0` | Set `1` when served over HTTPS (production). |
| `SESSION_LIFETIME_HOURS` | `168` | How long a login stays valid. |
| `MAX_UPLOAD_MB` | `200` | Max upload size for photos/videos. |
| `DASHBOARD_CORS_ORIGINS` | `*` | Comma-separated allowed origins for Socket.IO. Lock this down in production. |
| `LOGIN_MAX_ATTEMPTS` | `8` | Failed logins per IP before lockout. |
| `LOGIN_WINDOW_SECONDS` | `300` | Sliding window for counting failures. |
| `LOGIN_LOCKOUT_SECONDS` | `300` | Lockout duration after too many failures. |
| `MIN_PASSWORD_LENGTH` | `6` | Minimum password length for new accounts. |
| `COMMANDER_USERNAME` / `COMMANDER_PASSWORD` | `admin` / `admin` | Bootstrap admin, only used when no accounts exist. |
| `GEMINI_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `JAMENDO_CLIENT_ID` | — | Free feature keys (also editable in the ⚙️ Settings UI). |

## 5. Security model

- **Passwords** are stored as salted hashes (`werkzeug.security`), never plaintext.
- **Sessions** use signed cookies with `HttpOnly` + `SameSite=Lax`, and `Secure`
  when `SESSION_COOKIE_SECURE=1`. Sessions expire after `SESSION_LIFETIME_HOURS`.
- **Brute-force protection**: repeated failed logins from an IP are rate-limited
  and temporarily locked out (in-memory, per node — see `dashboard/security.py`).
- **Uploads** are size-capped (`MAX_UPLOAD_MB`) and restricted to known image/video
  extensions; oversized uploads return a clean `413` JSON error.
- **API errors** always return JSON (`401/404/413/500`) instead of stack traces.
- **Health endpoint** `/healthz` is unauthenticated and returns service status.

### Production checklist
- [ ] Change the default `admin` password.
- [ ] Set a strong `DASHBOARD_SECRET_KEY` (or let it auto-generate & persist).
- [ ] Set `SESSION_COOKIE_SECURE=1` (HTTPS).
- [ ] Restrict `DASHBOARD_CORS_ORIGINS` to your domain.
- [ ] Keep API keys in the platform's env/secret store, not in code.
