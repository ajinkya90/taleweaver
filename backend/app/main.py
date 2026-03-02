from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.config import router as config_router

app = FastAPI(title="Audio Story Creator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
