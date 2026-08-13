# Job & Claim Tracker

A small personal web app (Python/Flask) for tracking:

- **Claim Weeks** — the weekly CA EDD certification periods from your spreadsheet's "Date" table (week number, start/end date, EDD confirmation, EDD reported-consulting), with jobs-applied and consulting totals rolled up automatically.
- **Job Applications** — company, position, status, and the actual **resume, cover letter, and job description** files you used, stored in cloud object storage and downloadable later.
- **Consulting** — engagements with hours and earnings, rolled into the week they fall in so you can cross-check against what you report to EDD.

It's built to be a single-user app: you sign in with your GitHub account, and only the username(s) you list in `ALLOWED_GITHUB_USERNAMES` are allowed in.

## Tech stack

- **Flask** (app factory pattern, blueprints per feature)
- **SQLAlchemy + Flask-Migrate** — Postgres in production, SQLite locally
- **Authlib** — GitHub OAuth login
- **boto3** — file uploads to an S3-compatible bucket (Cloudflare R2 by default; AWS S3 works too)
- **Render** — hosting (web service + managed Postgres), via `render.yaml`

## Project layout

```
app/
  auth/          GitHub OAuth login/logout
  claims/        Claim weeks list/detail, EDD toggle buttons, week-lookup helper
  applications/  Job application CRUD + file upload/download
  consulting/    Consulting entry CRUD
  dashboard/     Home page summary
  templates/, static/
  models.py      ClaimWeek, JobApplication, ConsultingEntry, User
  storage.py     S3/R2 upload/download helper
  config.py      All settings, read from environment variables
scripts/
  import_from_excel.py   One-time importer for your original .xlsx "Date" table
migrations/      Flask-Migrate/Alembic migrations
wsgi.py          Entry point (`flask run` / gunicorn use this)
render.yaml      Render Blueprint (web service + Postgres)
tests/smoke_test.py   End-to-end smoke test (login gate, CRUD, week totals)
```

## How the data lines up with your spreadsheet

| Your spreadsheet table | App equivalent |
|---|---|
| `Date` (ISO Week No, Start/End Date, totals, EDD checkboxes) | `ClaimWeek` model, one row per week |
| `Job applications` (Application Date, Company, Position) | `JobApplication` model — plus status, notes, and resume/cover letter/job description file attachments |
| `Consulting` (Description, Start/End Date, Hours, Earned) | `ConsultingEntry` model |

Every job application and consulting entry is automatically linked to the `ClaimWeek` its date falls into, so the weekly "jobs applied" and "consulting hours/earned" totals you had as formulas in Excel are now computed live on the Claim Weeks page and week detail page — no manual summing.

**Note on consulting spanning weeks:** a consulting entry links to the week its *start date* falls in. If a single engagement crosses a week boundary, log it as two entries (one per week) so the weekly totals stay accurate for EDD reporting.

---

## 1. Local setup in VS Code

1. Open the project folder in VS Code.
2. Create and activate a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
   In VS Code, select this interpreter via **Python: Select Interpreter** (bottom right, or Cmd/Ctrl+Shift+P).
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy the environment template and fill it in (see sections 2 and 3 below for where the GitHub and R2 values come from):
   ```
   cp .env.example .env
   ```
   For a first local run you can leave `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` as placeholders — everything except the "Sign in with GitHub" button will still work with a manual test session, but you'll want real credentials before actually using the app day to day.
5. Initialize the database (SQLite, local file at `instance/jobtracker.db`) and load your claim weeks:
   ```
   export FLASK_APP=wsgi.py
   flask db upgrade
   flask seed-weeks
   ```
   `flask seed-weeks` generates 53 weekly rows starting at `BENEFIT_YEAR_START` (defaults to `2025-12-29`, matching your spreadsheet). If you'd rather import the exact rows from your original Excel file (in case you've since edited it), run instead:
   ```
   python scripts/import_from_excel.py "/path/to/Job Tracker App.xlsx"
   ```
6. Run it:
   ```
   flask run
   ```
   Visit `http://127.0.0.1:5000`.

Run the smoke test any time after setup to confirm everything still works end to end:
```
python tests/smoke_test.py
```

---

## 2. GitHub OAuth login setup

1. Go to [github.com/settings/developers](https://github.com/settings/developers) → **OAuth Apps** → **New OAuth App**.
2. Fill in the app name (e.g. "Job & Claim Tracker") and homepage URL (your local or Render URL).
3. Set **Authorization callback URL**:
   - `http://127.0.0.1:5000/auth/callback` (local dev)
   - `https://<your-render-app-name>.onrender.com/auth/callback` (production — add/update this once you know your Render URL from step 4 below; GitHub OAuth Apps only allow one callback URL, so you'll need to swap it when moving between local and prod, or create a second OAuth App for production)
4. Copy the generated **Client ID** and **Client Secret** into `.env` (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`) locally, and into Render's environment variables in production.
5. Set `ALLOWED_GITHUB_USERNAMES=your-github-username` (comma-separate more usernames if you ever want to add someone).

---

## 3. File storage setup (Cloudflare R2)

Cloudflare R2 is S3-compatible and has a generous free tier (10 GB storage, no egress fees) — plenty for resumes/cover letters/job descriptions.

1. Sign up / log in at [dash.cloudflare.com](https://dash.cloudflare.com), go to **R2 Object Storage**, and create a bucket (e.g. `job-tracker-files`).
2. Under **Manage R2 API Tokens**, create a token with **Object Read & Write** permission scoped to that bucket. Note the **Access Key ID**, **Secret Access Key**, and the **Account ID** (used to build the endpoint URL).
3. Fill in `.env` / Render environment variables:
   ```
   S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
   S3_ACCESS_KEY_ID=...
   S3_SECRET_ACCESS_KEY=...
   S3_BUCKET_NAME=job-tracker-files
   S3_REGION=auto
   ```

Prefer AWS S3 instead? Leave `S3_ENDPOINT_URL` blank, set `S3_REGION` to your bucket's region (e.g. `us-west-2`), and use an IAM user's access key/secret scoped to that bucket — the same `boto3` code path handles both since R2 speaks the S3 API.

---

## 4. Push to GitHub

```
git init
git add .
git commit -m "Initial commit: job & claim tracker"
gh repo create job-claim-tracker --private --source=. --push
```
(No `gh` CLI? Create an empty repo on github.com, then `git remote add origin <url>` and `git push -u origin main`.)

`.gitignore` already excludes `.env`, `instance/`, and `.venv/` so no secrets or local DB files get committed.

---

## 5. Deploy to Render

**Option A — Blueprint (recommended, uses `render.yaml`):**

1. Push the repo to GitHub (step 4).
2. In the [Render dashboard](https://dashboard.render.com/), click **New → Blueprint**, connect your GitHub account, and select this repo. Render reads `render.yaml` and provisions both the web service and a free Postgres database automatically.
3. When prompted, fill in the environment variables marked `sync: false` in `render.yaml`: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `ALLOWED_GITHUB_USERNAMES`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`.
4. Deploy. Render runs `flask db upgrade` automatically on every deploy (see `startCommand` in `render.yaml`), so the database schema is always up to date.
5. Note the live URL (`https://job-tracker-app-xxxx.onrender.com`), and set `<that-url>/auth/callback` as the GitHub OAuth App's **Authorization callback URL** (step 2.3 above).
6. One-time: seed the claim weeks in production. In the Render dashboard, open your web service's **Shell** tab and run:
   ```
   flask seed-weeks
   ```
   or, to import the exact rows from your Excel file, upload it into the shell session or run the importer against a `DATABASE_URL` pointed at production from your machine.

**Option B — manual setup:** create a Postgres instance and a Web Service pointing at this repo by hand, using `requirements.txt` for the build command and `flask db upgrade && gunicorn wsgi:app` as the start command, then set the same environment variables listed above.

**Free-tier notes:** Render's free web services spin down after 15 minutes of inactivity (the next visit takes ~30–50 seconds to wake up), and the free Postgres database expires after 90 days unless upgraded to a paid plan — worth knowing since this tracks something you need reliably for months. If that's a problem, Render's cheapest paid web service + database tier removes both limits for a few dollars a month.

---

## Customizing

- **Application statuses**: edit the list in `app/models.py` (`JobApplication.STATUSES`) and `app/applications/forms.py`.
- **Benefit year length/start**: change `BENEFIT_YEAR_START` / `BENEFIT_YEAR_WEEKS` env vars, then re-run `flask seed-weeks` (it skips weeks that already exist, so it's safe to re-run).
- **Styling**: everything is in `app/static/css/style.css`, plain CSS, no build step.
- **Adding a chart/report view**: the totals are already computed as model properties (`ClaimWeek.jobs_applied_count`, `.total_consulting_hours`, `.total_consulting_earned`) so a new template/route can reuse them directly.
