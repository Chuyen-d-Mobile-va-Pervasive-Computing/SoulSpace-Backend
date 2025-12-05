import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db

# Common routers
from app.api.user_admin_auth_router import router as user_admin_auth_router
from app.api.expert.expert_auth_router import router as expert_auth_router

# User routers
from app.api.user.journal_router import router as journal_router
from app.api.user.anon_post_router import router as anon_post_router
from app.api.user.anon_comment_router import router as anon_comment_router
from app.api.user.anon_like_router import router as anon_like_router
from app.api.user.reminder_router import router as reminder_router
from app.api.user.test_router import router as test_router
from app.api.user.user_tree_router import router as user_tree_router
from app.api.user.game_router import router as game_router
from app.api.user.badge_router import router as badge_router

# Admin routers
from app.api.admin.admin_router import router as admin_router
from app.api.admin.expert_management_router import router as expert_management_router

# Expert routers (placeholder)
from app.api.expert.expert_router import router as expert_router

app = FastAPI(title="SoulSpace Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# Common routes
app.include_router(user_admin_auth_router, prefix=API_PREFIX)
app.include_router(expert_auth_router, prefix=API_PREFIX)

# User routes
app.include_router(journal_router, prefix=API_PREFIX)
app.include_router(anon_post_router, prefix=API_PREFIX)
app.include_router(anon_comment_router, prefix=API_PREFIX)
app.include_router(anon_like_router, prefix=API_PREFIX)
app.include_router(reminder_router, prefix=API_PREFIX)
app.include_router(test_router, prefix=API_PREFIX)
app.include_router(user_tree_router, prefix=API_PREFIX)
app.include_router(game_router, prefix=API_PREFIX)
app.include_router(badge_router, prefix=API_PREFIX)

# Admin routes
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(expert_management_router, prefix=API_PREFIX)

# Expert routes (placeholder)
app.include_router(expert_router, prefix=API_PREFIX)


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
