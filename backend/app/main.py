import logging
import secrets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.config import settings
from app.routes.config import router as config_router
from app.routes.story import router as story_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Taleweaver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_allowed_emails() -> set:
    if not settings.allowed_emails:
        return set()
    return {e.strip().lower() for e in settings.allowed_emails.split(",") if e.strip()}


def _verify_google_token(token: str) -> dict:
    """Verify a Google ID token and return the payload."""
    return google_id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.google_client_id
    )


@app.middleware("http")
async def check_auth(request: Request, call_next):
    # Skip auth for OPTIONS, health, and non-API routes
    if request.method == "OPTIONS" or not request.url.path.startswith("/api") or request.url.path == "/api/health":
        return await call_next(request)

    # No auth configured — allow all (local dev / testing)
    if not settings.google_client_id and not settings.app_password:
        return await call_next(request)

    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if not token:
        token = request.query_params.get("token", "")

    if not token:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    # Strategy 1: Google Sign-In (if configured)
    if settings.google_client_id:
        try:
            payload = _verify_google_token(token)
            email = payload.get("email", "").lower()
            allowed = _get_allowed_emails()
            if allowed and email not in allowed:
                return JSONResponse(status_code=403, content={"detail": "Email not authorized"})
            request.state.user_email = email
            return await call_next(request)
        except Exception:
            # Token wasn't a valid Google token — fall through to password check
            pass

    # Strategy 2: APP_PASSWORD fallback (for local dev or simple deployments)
    if settings.app_password:
        if secrets.compare_digest(token, settings.app_password):
            return await call_next(request)

    return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})


app.include_router(config_router)
app.include_router(story_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
