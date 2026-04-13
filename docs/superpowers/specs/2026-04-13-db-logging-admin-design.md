# Database Logging + Admin Panel — Design Spec

## Overview

Add a Postgres database to log every story generation (inputs, prompt, output) and manage the email allowlist. Add an admin page to the frontend for viewing story logs and managing allowed emails.

## Database

### Provider
- Render free-tier Postgres, Oregon region (same as backend)
- Connection via `DATABASE_URL` env var (Render auto-provisions this when linking the DB to the service)

### Library
- `asyncpg` — lightweight async Postgres driver, no ORM
- Connection pool created on FastAPI startup, closed on shutdown

### Schema

```sql
CREATE TABLE IF NOT EXISTS allowed_emails (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stories (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL,
    user_email TEXT NOT NULL,
    story_type TEXT NOT NULL,         -- 'custom' or 'historical'
    kid_name TEXT NOT NULL,
    kid_age INTEGER NOT NULL,
    genre TEXT,                        -- null for historical
    event_id TEXT,                     -- null for custom
    description TEXT,                  -- null for historical
    mood TEXT,
    length TEXT,
    prompt TEXT NOT NULL,              -- full assembled LLM prompt
    title TEXT NOT NULL,
    story_text TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Tables are auto-created on app startup via `CREATE TABLE IF NOT EXISTS`.

### Migration from env var

On first deploy, seed `allowed_emails` table from the existing `ALLOWED_EMAILS` env var. After confirming the DB works, the env var can be removed. The seeding logic runs on startup: if the table is empty and `ALLOWED_EMAILS` is set, insert those emails.

## Backend Changes

### New file: `app/db.py`
- `init_db()` — create asyncpg connection pool, run CREATE TABLE statements
- `close_db()` — close the pool
- `get_allowed_emails() -> set[str]` — query all emails from `allowed_emails`
- `add_allowed_email(email: str)` — insert email
- `remove_allowed_email(email: str)` — delete email
- `log_story(...)` — insert into `stories` table
- `get_stories(limit, offset) -> list[dict]` — paginated query for admin view
- `get_story(id) -> dict` — single story detail

### Modified: `app/main.py`
- Call `init_db()` on startup, `close_db()` on shutdown via FastAPI lifespan
- Replace `_get_allowed_emails()` (reads env var) with `db.get_allowed_emails()` (queries DB)
- Add `ADMIN_EMAILS` env var (comma-separated). Admin check: `request.state.user_email in admin_emails`
- Keep `ALLOWED_EMAILS` env var as fallback seed source during migration

### Modified: `app/graph/nodes/story_writer.py`
- Return the assembled `prompt` string in the node output dict so it flows through the pipeline state
- Add `prompt` field: `return {"story_text": story_text, "title": title, "prompt": prompt}`

### Modified: `app/graph/state.py`
- Add `prompt: str` field to `StoryState` TypedDict

### Modified: `app/routes/story.py`
- After pipeline completes successfully in `run_pipeline()`, call `db.log_story()` with all fields
- Pass `user_email` into the pipeline run (from `request.state.user_email`)

### New file: `app/routes/admin.py`
- Protected by admin email check (decorator or dependency that checks `request.state.user_email` against `ADMIN_EMAILS`)
- Endpoints:
  - `GET /api/admin/emails` — list all allowed emails
  - `POST /api/admin/emails` — add email `{"email": "..."}`
  - `DELETE /api/admin/emails/{email}` — remove email
  - `GET /api/admin/stories` — paginated story log (query params: `limit`, `offset`). Returns all fields except `story_text` and `prompt` (for list view performance).
  - `GET /api/admin/stories/{id}` — full story detail including `prompt` and `story_text`
  - `GET /api/admin/me` — returns `{"email": "...", "is_admin": true}` for the current user (frontend uses this to show/hide admin link)

## Frontend Changes

### Modified: `src/api/client.ts`
- Add admin API functions:
  - `fetchAdminMe()` — GET `/api/admin/me`
  - `fetchAllowedEmails()` — GET `/api/admin/emails`
  - `addAllowedEmail(email)` — POST `/api/admin/emails`
  - `removeAllowedEmail(email)` — DELETE `/api/admin/emails/{email}`
  - `fetchStories(limit, offset)` — GET `/api/admin/stories`
  - `fetchStory(id)` — GET `/api/admin/stories/{id}`

### New: `src/components/AdminScreen.tsx`
- Route: when user navigates to admin (e.g., gear icon or `/admin` path)
- Two tabs:
  1. **Emails** — table of allowed emails with add (text input + button) and remove (delete button per row)
  2. **Stories** — paginated table showing: timestamp, user_email, kid_name, kid_age, story_type, genre/event, mood, title. Click a row to expand and see the full `prompt` and `story_text`.
- Styled consistently with existing glassmorphism theme

### Modified: `src/App.tsx`
- On login, call `fetchAdminMe()` to check if user is admin
- If admin, show a small admin link/icon (e.g., gear icon in corner) that navigates to AdminScreen
- Non-admin users never see the admin link; direct navigation to admin endpoints returns 403

## New Environment Variables

### Backend (Render)
```
DATABASE_URL=                    # Auto-set by Render when linking Postgres
ADMIN_EMAILS=ajinkya90@gmail.com # Comma-separated admin emails
```

## Auth Flow Summary

1. User signs in with Google (unchanged)
2. Backend middleware verifies Google token, extracts email
3. Email checked against `allowed_emails` DB table (instead of env var)
4. For admin endpoints: additional check that email is in `ADMIN_EMAILS` env var
5. Frontend checks `GET /api/admin/me` after login to conditionally show admin UI

## What This Does NOT Change

- Audio generation pipeline (unchanged)
- Job store (still in-memory, not moved to DB — jobs are ephemeral)
- Google Sign-In flow (unchanged)
- Frontend story creation flow (unchanged)
- File-based transcript logging in `story_writer.py` (can be removed later, DB replaces it)
