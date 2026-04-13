"""Database module — asyncpg pool, allowed-emails CRUD, story logging."""

from __future__ import annotations

import logging
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_emails(raw: Optional[str]) -> set[str]:
    """Parse a comma-separated email string into a lowercase set."""
    if not raw:
        return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _get_admin_emails() -> set[str]:
    """Return the set of admin emails from settings."""
    return _parse_emails(settings.admin_emails)


# ---------------------------------------------------------------------------
# Pool lifecycle
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Create the asyncpg connection pool, ensure tables exist, and seed."""
    global _pool

    if not settings.database_url:
        logger.warning("DATABASE_URL not set — running without Postgres")
        return

    _pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=5,
    )

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS allowed_emails (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id SERIAL PRIMARY KEY,
                job_id UUID NOT NULL,
                user_email TEXT NOT NULL,
                story_type TEXT NOT NULL,
                kid_name TEXT NOT NULL,
                kid_age INTEGER NOT NULL,
                genre TEXT,
                event_id TEXT,
                description TEXT,
                mood TEXT,
                length TEXT,
                prompt TEXT NOT NULL,
                title TEXT NOT NULL,
                story_text TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Seed allowed_emails from env var if table is empty
        count = await conn.fetchval("SELECT COUNT(*) FROM allowed_emails")
        if count == 0:
            seed_emails = _parse_emails(settings.allowed_emails)
            if seed_emails:
                for email in seed_emails:
                    await conn.execute(
                        "INSERT INTO allowed_emails (email) VALUES ($1) ON CONFLICT DO NOTHING",
                        email,
                    )
                logger.info("Seeded %d allowed emails from env var", len(seed_emails))

    logger.info("Database pool initialised")


async def close_db() -> None:
    """Close the asyncpg pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


# ---------------------------------------------------------------------------
# Allowed-emails CRUD
# ---------------------------------------------------------------------------

async def get_allowed_emails() -> set[str]:
    """Return the set of allowed emails. Falls back to env var if no pool."""
    if not _pool:
        return _parse_emails(settings.allowed_emails)

    async with _pool.acquire() as conn:
        rows = await conn.fetch("SELECT email FROM allowed_emails")
        return {row["email"] for row in rows}


async def add_allowed_email(email: str) -> bool:
    """Insert an allowed email. Returns True if inserted, False if duplicate."""
    if not _pool:
        return False
    email = email.strip().lower()
    async with _pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO allowed_emails (email) VALUES ($1)",
                email,
            )
            return True
        except asyncpg.UniqueViolationError:
            return False


async def remove_allowed_email(email: str) -> bool:
    """Delete an allowed email. Returns True if a row was deleted."""
    if not _pool:
        return False
    email = email.strip().lower()
    async with _pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM allowed_emails WHERE email = $1",
            email,
        )
        return result == "DELETE 1"


async def list_allowed_emails() -> list[dict]:
    """Return list of dicts with id, email, added_at."""
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, email, added_at FROM allowed_emails ORDER BY added_at"
        )
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Story logging
# ---------------------------------------------------------------------------

async def log_story(
    *,
    job_id: str,
    user_email: str,
    story_type: str,
    kid_name: str,
    kid_age: int,
    genre: Optional[str] = None,
    event_id: Optional[str] = None,
    description: Optional[str] = None,
    mood: Optional[str] = None,
    length: Optional[str] = None,
    prompt: str,
    title: str,
    story_text: str,
    duration_seconds: int,
) -> None:
    """Insert a completed story into the stories table."""
    if not _pool:
        logger.warning("No DB pool — skipping story log for job %s", job_id)
        return

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO stories (
                job_id, user_email, story_type, kid_name, kid_age,
                genre, event_id, description, mood, length,
                prompt, title, story_text, duration_seconds
            ) VALUES (
                $1::uuid, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14
            )
            """,
            job_id, user_email, story_type, kid_name, kid_age,
            genre, event_id, description, mood, length,
            prompt, title, story_text, duration_seconds,
        )


async def get_stories(limit: int = 20, offset: int = 0) -> list[dict]:
    """Paginated query returning stories without story_text and prompt."""
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, job_id, user_email, story_type, kid_name, kid_age,
                   genre, event_id, description, mood, length,
                   title, duration_seconds, created_at
            FROM stories
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
        return [dict(row) for row in rows]


async def get_stories_count() -> int:
    """Return total number of stories."""
    if not _pool:
        return 0
    async with _pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM stories")


async def get_story(story_id: int) -> Optional[dict]:
    """Return full story dict including prompt and story_text."""
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM stories WHERE id = $1",
            story_id,
        )
        return dict(row) if row else None
