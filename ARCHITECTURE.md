# SoulSpace Backend - Role-Based Architecture

## Cấu Trúc Thư Mục Mới (Role-Based)

Dự án đã được tái cấu trúc theo mô hình phân quyền role-based với 4 nhóm chính:

### 1. **Common** - Chức năng chung (Authentication, Public API)
```
app/
├── api/common/
│   └── auth_router.py          # Authentication endpoints
├── services/common/
│   ├── auth_service.py         # Authentication business logic
│   └── email_service.py        # Email sending service
└── schemas/common/
    └── auth_schema.py          # Auth DTOs (register, login, etc)
```

### 2. **User** - Chức năng cho người dùng thường
```
app/
├── api/user/
│   ├── anon_post_router.py
│   ├── anon_comment_router.py
│   ├── anon_like_router.py
│   ├── journal_router.py
│   ├── game_router.py
│   ├── reminder_router.py
│   ├── badge_router.py
│   ├── user_tree_router.py
│   └── test_router.py
├── services/user/
│   ├── anon_post_service.py
│   ├── anon_comment_service.py
│   ├── anon_like_service.py
│   ├── journal_service.py
│   ├── game_service.py
│   ├── reminder_service.py
│   ├── badge_service.py
│   ├── user_tree_service.py
│   ├── test_service.py
│   └── user_test_result_service.py
└── schemas/user/
    ├── anon_post_schema.py
    ├── anon_comment_schema.py
    ├── journal_schema.py
    ├── game_schema.py
    ├── reminder_schema.py
    ├── badge_schema.py
    ├── user_tree_schema.py
    ├── test_schema.py
    └── user_test_result_schema.py
```

### 3. **Admin** - Chức năng quản trị (Placeholder)
```
app/
├── api/admin/
│   └── admin_router.py         # Admin endpoints (placeholder)
├── services/admin/             # Ready for admin services
└── schemas/admin/              # Ready for admin schemas
```

### 4. **Expert** - Chức năng chuyên gia tư vấn (Placeholder)
```
app/
├── api/expert/
│   └── expert_router.py        # Expert endpoints (placeholder)
├── services/expert/            # Ready for expert services
└── schemas/expert/             # Ready for expert schemas
```

### 5. **Shared Resources** (Không thay đổi)
```
app/
├── models/                     # Database models (MongoDB)
├── repositories/               # Data access layer
├── core/                       # Config, security, database
│   ├── permissions.py          # NEW: Role enum & decorators
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   └── dependencies.py
└── utils/                      # Utilities
```

---

## Hệ Thống Phân Quyền (Permissions)

### Role Enum
```python
from app.core.permissions import Role

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    EXPERT = "expert"
```

### Sử Dụng `@require_role` Decorator

```python
from app.core.permissions import Role, require_role
from app.core.dependencies import get_current_user

@router.get("/admin-only-endpoint")
@require_role(Role.ADMIN)
async def admin_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "Admin access granted"}

@router.get("/admin-or-expert")
@require_role(Role.ADMIN, Role.EXPERT)
async def multi_role_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "Admin or Expert access"}
```

### Check Role Programmatically
```python
from app.core.permissions import check_role, Role

if check_role(current_user, Role.ADMIN):
    # Do admin stuff
    pass
```

---

## Import Patterns

### Router imports Service và Schema
```python
# Old (deprecated)
from app.services.journal_service import JournalService
from app.schemas.journal_schema import JournalCreate

# New (correct)
from app.services.user.journal_service import JournalService
from app.schemas.user.journal_schema import JournalCreate
```

### Service imports Schema
```python
# Old (deprecated)
from app.schemas.journal_schema import JournalCreate

# New (correct)
from app.schemas.user.journal_schema import JournalCreate
```

### Main.py imports Router
```python
# Common
from app.api.common.auth_router import router as auth_router

# User
from app.api.user.journal_router import router as journal_router
from app.api.user.game_router import router as game_router

# Admin
from app.api.admin.admin_router import router as admin_router

# Expert
from app.api.expert.expert_router import router as expert_router
```

---

## API Endpoints Structure

### Common Routes
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`

### User Routes
- `POST /api/v1/journal` (create journal)
- `GET /api/v1/anon-posts` (list anonymous posts)
- `POST /api/v1/game/session` (start game)
- `GET /api/v1/badges` (list badges)
- etc...

### Admin Routes (Placeholder)
- `GET /api/v1/admin/health` (health check)
- `GET /api/v1/admin/info` (requires admin role)

### Expert Routes (Placeholder)
- `GET /api/v1/expert/health` (health check)
- `GET /api/v1/expert/info` (requires expert role)

---

## Migration Checklist

✅ **Completed:**
1. Tạo cấu trúc thư mục role-based (common, user, admin, expert)
2. Di chuyển routers, services, schemas vào thư mục tương ứng
3. Cập nhật tất cả imports trong routers và services
4. Cập nhật `app/main.py` để import từ vị trí mới
5. Thêm `app/core/permissions.py` với Role enum và decorators
6. Tạo placeholder routers cho admin và expert
7. Giữ nguyên 100% logic code, chỉ thay đổi cấu trúc thư mục

⏳ **Chưa làm (để sau):**
- Implement các endpoint admin cụ thể
- Implement các endpoint expert cụ thể
- Thêm role field vào User model (đã có trong auth_schema)
- Cập nhật tests theo cấu trúc mới

---

## Run Application

```bash
# Set environment variable (Windows PowerShell)
$env:TRANSFORMERS_NO_TF="1"

# Run with uvicorn
uvicorn app.main:app --reload
```

---

## Notes

- **Backward Compatible**: API endpoints paths không đổi, chỉ thay đổi internal structure
- **No Breaking Changes**: Logic code 100% giữ nguyên
- **Ready for Expansion**: Dễ dàng thêm admin/expert features trong tương lai
- **Clear Separation**: Mỗi role có namespace riêng, dễ quản lý và mở rộng

---

**Cập nhật:** 03/12/2025  
**Phiên bản:** 2.0.0 (Role-Based Architecture)
