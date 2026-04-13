# Story Library — Design Spec

## Overview

Let each authenticated user view and replay their past stories. Audio is stored as bytes in Postgres alongside existing story metadata.

## Database

### Schema change

Add column to existing `stories` table:

```sql
ALTER TABLE stories ADD COLUMN audio_data BYTEA;
```

On startup, use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (or check `information_schema.columns`) to add the column idempotently. Existing rows will have `NULL` audio_data (stories generated before this feature).

Typical MP3 size: 3-5MB per story. Render free Postgres: 256MB. Capacity: ~50-80 stories with audio.

## Backend Changes

### Modified: `app/db.py`

- `log_story()` — add `audio_data: bytes` parameter. Store in the new column.
- `init_db()` — add the `audio_data` column if it doesn't exist.
- New: `get_user_stories(user_email, limit, offset) -> list[dict]` — paginated query returning id, title, kid_name, kid_age, story_type, genre, event_id, duration_seconds, created_at. Filtered by `user_email`. Does NOT return audio_data, prompt, or story_text (list view).
- New: `get_user_stories_count(user_email) -> int` — total count for pagination.
- New: `get_user_story(story_id, user_email) -> dict | None` — full story detail including story_text and transcript. Filtered by user_email for access control. Does NOT return audio_data (fetched separately).
- New: `get_story_audio(story_id) -> bytes | None` — returns just the audio_data bytes for a story.

### Modified: `app/routes/story.py`

- In `run_pipeline()`, pass `final_audio` bytes to `db.log_story()`.

### New: `app/routes/my_stories.py`

Protected by existing auth middleware (requires `request.state.user_email`).

- `GET /api/my-stories` — paginated list of current user's stories. Query params: `limit` (default 20, max 100), `offset` (default 0). Returns: `{stories: [...], total, limit, offset}`.
- `GET /api/my-stories/{id}` — full story detail (title, story_text, duration, metadata). Returns 404 if story doesn't exist or belongs to a different user.
- `GET /api/my-stories/{id}/audio` — streams MP3 bytes. Returns 404 if story doesn't exist, doesn't belong to user, or has no audio_data.

### Modified: `app/routes/admin.py`

- `GET /api/admin/stories/{id}/audio` — admin can stream audio for any story (for debugging). Returns 404 if no audio_data.

### Modified: `app/main.py`

- Register `my_stories` router.

## Frontend Changes

### New types in `src/types/index.ts`

```typescript
export interface MyStoryEntry {
  id: number;
  title: string;
  kid_name: string;
  kid_age: number;
  story_type: string;
  genre: string | null;
  event_id: string | null;
  duration_seconds: number;
  created_at: string;
}

export interface MyStoryDetail extends MyStoryEntry {
  story_text: string;
  mood: string | null;
  length: string | null;
  description: string | null;
}

export interface MyStoriesResponse {
  stories: MyStoryEntry[];
  total: number;
  limit: number;
  offset: number;
}
```

### New API functions in `src/api/client.ts`

- `fetchMyStories(limit, offset) -> MyStoriesResponse`
- `fetchMyStory(id) -> MyStoryDetail`
- `getMyStoryAudioUrl(id) -> string` — returns URL with auth token as query param (same pattern as `getAudioUrl`)

### New: `src/components/MyStoriesScreen.tsx`

- List of past stories: title, kid name, date, duration
- Click a row to expand: shows audio player + transcript (same playback pattern as StoryScreen)
- Pagination (prev/next) if more than 20 stories
- "No stories yet" empty state
- Styled consistently with existing glassmorphism theme

### Modified: `src/App.tsx`

- Add `showMyStories` state
- "My Stories" button visible below the header after login
- When toggled, shows MyStoriesScreen instead of the main flow (same conditional pattern as admin)
- If user is on MyStoriesScreen and clicks "Taleweaver" title, goes back to main app

## New API Endpoints Summary

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/my-stories` | GET | List current user's stories (paginated) |
| `/api/my-stories/{id}` | GET | Full story detail for current user |
| `/api/my-stories/{id}/audio` | GET | Stream MP3 audio for current user's story |
| `/api/admin/stories/{id}/audio` | GET | Stream MP3 audio for any story (admin only) |

## Auth

- `/api/my-stories` endpoints use `request.state.user_email` from existing auth middleware
- Each user can only access their own stories
- Admin can access any story's audio via the admin endpoint

## What This Does NOT Include

- Deleting stories from the library
- Sharing stories between users
- Re-generating audio for old stories
- Storing audio for stories generated before this feature (they will show "no audio available")
