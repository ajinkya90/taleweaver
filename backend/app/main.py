import logging
import secrets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes.config import router as config_router
from app.routes.story import router as story_router

app = FastAPI(title="Taleweaver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def check_app_password(request: Request, call_next):
    if settings.app_password and request.url.path.startswith("/api") and request.url.path != "/api/health":
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        # Also accept token as query param (needed for audio element src URLs)
        if not token:
            token = request.query_params.get("token", "")
        if not secrets.compare_digest(token, settings.app_password):
            return JSONResponse(status_code=401, content={"detail": "Invalid password"})
    return await call_next(request)


app.include_router(config_router)
app.include_router(story_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
