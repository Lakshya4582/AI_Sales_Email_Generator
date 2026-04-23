# AI Sales Email Generator

A web app that helps sales teams draft cold emails, follow-ups, and subject-line variants using an LLM — runs entirely on your own machine via [Ollama](https://ollama.com/) by default (free), or against OpenAI / Gemini / Anthropic / any OpenAI-compatible provider.

## Features

- 📧 **Cold email generator** — product + audience + tone + length → polished email with subject, body, CTA
- 🔁 **Follow-up generator** — pick any past email, enter days since sent, get a polite follow-up
- 💡 **Subject line brainstorm** — 5 different angles (benefit, curiosity, specific, pain, casual)
- ✍️ **Email improver** — paste your own draft, get a polished rewrite
- 👤 **Accounts** — signup / login, per-user email history with view/follow-up/delete
- 🔌 **Provider-agnostic** — swap Ollama for OpenAI/Gemini/Claude with 3 lines in `.env`

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Auth:** bcrypt password hashing + JWT (PyJWT)
- **Frontend:** plain HTML / CSS / vanilla JS (no framework, no build step)
- **LLM:** Ollama (default) via the OpenAI SDK's compatible endpoint

## Setup

```bash
# 1. Create venv and install deps
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements.txt

# 2. Install Ollama and pull a model
#    https://ollama.com/download
ollama pull llama3.2:3b

# 3. Copy .env.example to .env (or create .env manually — see Configuration below)

# 4. Start the backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 5. Open frontend/signup.html in your browser
```

## Configuration

All settings live in `.env`. Minimum required:

```
# LLM backend (Ollama default)
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2:3b

# Auth
AUTH_SECRET=<random 64-byte string — generate with: python -c "import secrets; print(secrets.token_urlsafe(64))">
DATABASE_URL=sqlite:///./app.db
```

### Switching LLM providers

No code change needed — just edit `.env`:

| Provider | `OPENAI_BASE_URL` | Model example |
|---|---|---|
| Ollama (local) | `http://localhost:11434/v1` | `llama3.2:3b` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |

Restart the backend after changing `.env`.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/signup` | public | Create account |
| POST | `/login` | public | Get bearer token |
| GET | `/me` | required | Current user profile |
| PATCH | `/me` | required | Update name/company/role |
| POST | `/change-password` | required | Change password |
| POST | `/generate-email` | required | New cold email |
| POST | `/follow-up` | required | Follow-up to a past email |
| POST | `/subject-lines` | required | 5 subject-line variants |
| POST | `/improve-email` | required | Rewrite a pasted draft |
| GET | `/history` | required | Your past emails |
| DELETE | `/history/{id}` | required | Delete one history entry |

## Project layout

```
backend/
  main.py       # FastAPI app, middleware, startup migrations
  routes.py     # All HTTP endpoints
  services.py   # LLM prompts + calls
  auth.py       # Password hashing, JWT, current_user dependency
  models.py     # ORM (User, EmailHistory) + Pydantic schemas
  db.py         # SQLAlchemy engine + session
frontend/
  index.html    # Main generator page (requires auth)
  login.html
  signup.html
  profile.html  # Edit account
  style.css
  script.js     # Generator + history + follow-up + subjects + improver
  auth.js       # Token storage, apiFetch wrapper
app.db          # SQLite DB (gitignored)
.env            # Config / secrets (gitignored)
```

## Status

This is an MVP. Built for learning and demoing; not yet production-ready — missing password reset, email verification, automated tests, and a real hosting setup.
