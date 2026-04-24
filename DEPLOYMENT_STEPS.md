# Deployment Guide — Step by Step

Follow these sections in order. Total time: **30–60 minutes** once your
accounts are set up. Everything here stays on **free tiers**.

> Pre-requisite: the code prep is already done (config.js, env-driven CORS,
> Postgres driver). You just need to create accounts, push code, and wire
> things up.

---

## Part A — Push your code to GitHub (~5 min)

### A1. Sign up / sign in
Go to https://github.com and create an account if you don't have one.

### A2. Create a new repo
- Click the green **"New"** button (or go to https://github.com/new).
- **Repository name:** `ai-sales-email-generator` (or anything).
- **Privacy:** Private is fine. Public is also fine — nothing secret is
  in the code because `.env` is gitignored.
- **Do NOT** add a README, .gitignore, or license (we already have them).
- Click **Create repository**.

### A3. Push your local code
Open a terminal in the project folder `D:\ai-sales-email-generator` and run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/Lakshya4582/AI_Sales_Email_Generator.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

**Verify:** refresh the GitHub repo page — you should see all the files
(but NOT `.env`, `venv/`, or `app.db` — those are gitignored and shouldn't
appear. If they do, stop and tell me.)

---

## Part B — Create Postgres DB on Supabase (~5 min, free forever)

### B1. Sign up
Go to https://supabase.com, sign up (GitHub login is fastest).

### B2. Create a project
- Click **"New project"**.
- **Name:** `ai-sales-email` (or anything).
- **Database password:** Generate a strong one — **save it somewhere
  safe, you'll need it in a minute**.
- **Region:** pick the closest to you (e.g. Mumbai for India).
- **Pricing plan:** Free.
- Click **Create new project**. Wait ~2 minutes for provisioning.

### B3. Get the connection string
- Once the project is ready, click **Project Settings** (gear icon) →
  **Database** (left sidebar).
- Scroll to **Connection string** section → **URI** tab.
- Copy the string. It looks like:
  ```
  postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghij.supabase.co:5432/postgres
  ```
- **Replace `[YOUR-PASSWORD]`** with the password you saved in B2.
- Keep this string handy — you'll paste it into Render next.

---

## Part C — Deploy backend on Render (~10 min, free)

### C1. Sign up
Go to https://render.com, sign up (GitHub login is fastest — it also
gives Render access to your repos, which you'll need).

### C2. Create a new Web Service
- Click **"New +"** → **"Web Service"**.
- Under **"Connect a repository"**, find your `ai-sales-email-generator`
  repo and click **Connect**. (If not visible: click "Configure account"
  and grant Render access.)

### C3. Configure the service
Fill in these fields:

| Field | Value |
|---|---|
| **Name** | `ai-email-backend` (this becomes part of your URL) |
| **Region** | Pick one near you (e.g. Singapore for India) |
| **Branch** | `main` |
| **Root Directory** | leave blank |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

### C4. Add environment variables (CRITICAL — don't skip)
Scroll to **Environment Variables**. Click **"Add Environment Variable"**
and add these **FIVE** (copy each exactly):

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | Your Gemini API key (starts `AIza…`) |
| `OPENAI_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `OPENAI_MODEL` | `gemini-2.5-flash` |
| `AUTH_SECRET` | The random secret from your `.env` (or generate a new one) |
| `DATABASE_URL` | The Supabase connection string from step B3 |

> **Don't set `FRONTEND_ORIGIN` yet** — we'll add it in Part E once we
> know the Vercel URL.

### C5. Deploy
Click **Create Web Service**. Render will:
1. Clone your repo
2. Run `pip install -r requirements.txt`
3. Start the server

Watch the log. First deploy takes 3–5 min. When you see
`Uvicorn running on http://0.0.0.0:XXXX`, it's live.

### C6. Copy your backend URL
At the top of the service page, you'll see a URL like
`https://ai-email-backend.onrender.com`. **Copy it — you need it in Part D.**

### C7. Smoke test
In your browser, open: `https://ai-email-backend.onrender.com/`
You should see: `{"message":"AI Email Generator Running"}`

---

## Part D — Deploy frontend on Vercel (~5 min, free)

### D1. Edit `frontend/config.js` with your Render URL
Open `frontend/config.js` in any editor. Find this line:
```js
return "https://CHANGE-ME-TO-YOUR-RENDER-BACKEND.onrender.com";
```
Replace `CHANGE-ME-TO-YOUR-RENDER-BACKEND.onrender.com` with your actual
Render URL (without the trailing slash). Example:
```js
return "https://ai-email-backend.onrender.com";
```

### D2. Commit and push the change
```bash
git add frontend/config.js
git commit -m "Point frontend to deployed backend"
git push
```

### D3. Sign up at Vercel
Go to https://vercel.com, sign up (GitHub login is fastest).

### D4. Import the project
- On the Vercel dashboard, click **"Add New…"** → **"Project"**.
- Find your `ai-sales-email-generator` repo and click **Import**.

### D5. Configure the project
| Field | Value |
|---|---|
| **Project Name** | `ai-sales-email` (or anything) |
| **Framework Preset** | **Other** |
| **Root Directory** | click **Edit** → set to `frontend` |
| **Build Command** | leave empty / default |
| **Output Directory** | leave empty / default (just serves the folder) |
| **Install Command** | leave empty / default |

No environment variables needed on Vercel.

### D6. Deploy
Click **Deploy**. ~30 seconds. When done you'll see a URL like
`https://ai-sales-email.vercel.app`. **Copy this URL.**

### D7. Open it and... expect it to not work yet
Open the Vercel URL → you should see the signup/login page load, but any
API call (signup, login) will **fail with CORS error** because the backend
doesn't know to trust your Vercel domain yet. That's what Part E fixes.

---

## Part E — Wire them together (~2 min)

### E1. Add FRONTEND_ORIGIN to Render
- Go back to your Render service → **Environment** tab.
- Click **Add Environment Variable**:

| Key | Value |
|---|---|
| `FRONTEND_ORIGIN` | `https://ai-sales-email.vercel.app` (your Vercel URL) |

- Click **Save Changes**. Render auto-redeploys (~2 min).

### E2. Test the full flow
Once Render finishes redeploying:

1. Open your Vercel URL → `https://ai-sales-email.vercel.app/signup.html`
2. Create a new account.
3. You should land on the main page with the email generator.
4. Generate an email — it should come back in 5–15 seconds (via Gemini).
5. Open it on your phone — same URL, same account works.

---

## 🎉 You're deployed

Your app is now live. Share the Vercel URL with anyone.

- **Frontend:** `https://ai-sales-email.vercel.app`
- **Backend:** `https://ai-email-backend.onrender.com`
- **Database:** Supabase (persists forever on free tier)
- **LLM:** Gemini 2.5 Flash (free tier)

**Total monthly cost:** $0.

---

## Common issues & fixes

### "Failed to fetch" on Vercel site
- Usually CORS. Double-check `FRONTEND_ORIGIN` on Render matches your
  Vercel URL exactly (with `https://`, no trailing slash).
- Check Render logs for errors.

### First request is very slow (30–60 seconds)
- Render free tier sleeps after 15 min idle. First request wakes it up.
- Subsequent requests are fast.
- Fix: upgrade to Render Starter ($7/month) for no-sleep.

### Getting 500 errors on generate
- Check Render logs → probably Gemini API key issue.
- Test your key directly: open https://aistudio.google.com/app/apikey
  and verify it still exists.
- Some models have per-project free-tier restrictions. `gemini-2.5-flash`
  works for new accounts; if blocked, try `gemini-1.5-flash` or
  `gemini-2.0-flash-exp`.

### Lost user accounts after a redeploy
- You accidentally used SQLite on Render (which has ephemeral disk).
  Check `DATABASE_URL` env var on Render points to your Supabase URL.

### Accidentally pushed `.env` or `app.db` to GitHub
- Rotate ALL secrets immediately (Gemini key, AUTH_SECRET, Supabase
  password).
- `git rm --cached .env app.db` → commit → push.
- Consider the repo compromised; move to a new repo if it was public.

---

## What to do after deploying

1. **Rotate your Gemini key** — it's been in our conversation. Create a
   new one at https://aistudio.google.com/app/apikey, update the Render
   env var, redeploy.
2. **Add a custom domain** (optional, ~$10/year) — Vercel + Cloudflare
   work seamlessly.
3. **Consider upgrading Render** if you get real users ($7/month to kill
   the sleep).
4. **Monitor** your Gemini usage at https://aistudio.google.com/app/usage
   so you know when you're close to the free-tier daily cap.
