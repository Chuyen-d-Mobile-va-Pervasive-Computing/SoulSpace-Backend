import uvicorn
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
from app.api.test_router import router as test_router
from app.api.user_tree_router import router as user_tree_router
from app.api.game_router import router as game_router
from app.api.badge_router import router as badge_router

app = FastAPI(title="SoulSpace Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(journal_router, prefix=API_PREFIX)
app.include_router(anon_post_router, prefix=API_PREFIX)
app.include_router(anon_comment_router, prefix=API_PREFIX)
app.include_router(anon_like_router, prefix=API_PREFIX)
app.include_router(reminder_router, prefix=API_PREFIX)
app.include_router(test_router, prefix=API_PREFIX)
app.include_router(user_tree_router, prefix=API_PREFIX)
app.include_router(game_router, prefix=API_PREFIX)
app.include_router(badge_router, prefix=API_PREFIX)


@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
