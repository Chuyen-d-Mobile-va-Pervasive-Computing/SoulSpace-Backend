from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.auth_router import router as auth_router
from app.api.journal_router import router as journal_router
from app.api.anon_post_router import router as anon_post_router
from app.api.anon_comment_router import router as anon_comment_router
from app.api.anon_like_router import router as anon_like_router
from app.api.reminder_router import router as reminder_router

app = FastAPI(title="SoulSpace Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(journal_router)
app.include_router(anon_post_router)
app.include_router(anon_comment_router)
app.include_router(anon_like_router)
app.include_router(reminder_router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
