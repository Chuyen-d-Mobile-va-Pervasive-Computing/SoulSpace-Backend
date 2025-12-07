# 📚 SoulSpace Backend - API Documentation (Community Features)

**Tài liệu API cho tính năng Cộng đồng**  
**Cập nhật**: December 7, 2025

---

## 📑 Mục lục

1. [User - Đăng bài viết](#-user---đăng-bài-viết)
2. [User - Comment](#-user---comment)
3. [User - Like/Unlike](#-user---likeunlike)
4. [User - Report](#-user---report)
5. [User - Cập nhật tài khoản](#-user---cập-nhật-tài-khoản)
6. [Admin - Quản lý bài viết](#-admin---quản-lý-bài-viết)
7. [Admin - Quản lý comments](#-admin---quản-lý-comments)
8. [Admin - Reports](#-admin---reports)
9. [Admin - Expert Articles](#-admin---expert-articles)
10. [Admin - Thống kê](#-admin---thống-kê)

---

## 📝 User - Đăng bài viết

### POST /api/v1/anon-posts/
**Tạo bài viết mới**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | user, expert |

**Input:**
```json
{
  "content": "Nội dung bài viết...",
  "is_anonymous": true,
  "hashtags": ["mental_health", "daily"]
}
```

| Field | Mô tả |
|-------|-------|
| `content` | 1-5000 ký tự |
| `is_anonymous` | `true` = ẩn danh (mặc định), `false` = hiển thị tên |
| `hashtags` | Mảng string, tùy chọn |

**Moderation tự động:**
- Nếu phát hiện từ khóa nhạy cảm → `Pending` (chờ duyệt)
- Nếu phát hiện từ khóa nguy hiểm → `Blocked` + gửi notification gợi ý liên hệ expert
- Nếu chứa link/số điện thoại → `Blocked`

**Output:**
```json
{
  "_id": "66f123...",
  "content": "...",
  "is_anonymous": true,
  "author_name": "Ẩn danh",
  "moderation_status": "Approved",
  "like_count": 0,
  "comment_count": 0,
  "is_liked": false,
  "is_owner": true
}
```

---

### GET /api/v1/anon-posts/
**Lấy danh sách bài viết cộng đồng**

| Yêu cầu | |
|---------|--|
| Auth | Optional (nếu có sẽ hiện is_liked, is_owner) |

**Query params:**
- `limit` (int, default=20, max=100)

**Output:** Mảng bài viết đã được duyệt (`moderation_status = "Approved"`)

---

### GET /api/v1/anon-posts/my-posts
**Lấy bài viết của mình (bao gồm Pending, Blocked)**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |

---

### GET /api/v1/anon-posts/{post_id}
**Chi tiết một bài viết**

---

### DELETE /api/v1/anon-posts/{post_id}
**Xóa bài viết của mình**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Điều kiện | Chỉ owner mới được xóa |

---

## 💬 User - Comment

### POST /api/v1/anon-comments/
**Tạo bình luận**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |

**Input:**
```json
{
  "post_id": "66f123...",
  "content": "Cảm ơn bạn đã chia sẻ!",
  "is_preset": false
}
```

| Field | Mô tả |
|-------|-------|
| `post_id` | ID bài viết |
| `content` | Nội dung bình luận |
| `is_preset` | `true` nếu dùng bình luận mẫu |

---

### GET /api/v1/anon-comments/{post_id}
**Lấy danh sách bình luận của một bài viết**

---

### DELETE /api/v1/anon-comments/{comment_id}
**Xóa bình luận của mình**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Điều kiện | Chỉ owner mới được xóa |

---

## ❤️ User - Like/Unlike

### POST /api/v1/anon-likes/{post_id}
**Like bài viết**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |

**Output:**
```json
{
  "message": "Liked",
  "like_count": 5
}
```

---

### DELETE /api/v1/anon-likes/{post_id}
**Unlike bài viết**

---

## 🚩 User - Report

### POST /api/v1/reports/
**Báo cáo bài viết/bình luận vi phạm**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |

**Input:**
```json
{
  "target_id": "66f123...",
  "target_type": "post",
  "reason": "Nội dung không phù hợp"
}
```

| Field | Mô tả |
|-------|-------|
| `target_id` | ID của post hoặc comment |
| `target_type` | `"post"` hoặc `"comment"` |
| `reason` | Lý do báo cáo |

---

## 👤 User - Cập nhật tài khoản

### GET /api/v1/auth/me
**Lấy thông tin tài khoản hiện tại**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |

**Output:**
```json
{
  "id": "66f123...",
  "username": "SoulSky_1234",
  "email": "user@example.com",
  "role": "user",
  "avatar_url": "https://cloudinary.com/avatar.jpg",
  "total_points": 150,
  "created_at": "2025-12-01T10:00:00Z",
  "last_login_at": "2025-12-07T14:00:00Z"
}
```

---

### POST /api/v1/auth/update-username
**Cập nhật username**

**Input:**
```json
{
  "new_username": "MyNewName"
}
```

| Validation |
|------------|
| 3-30 ký tự |
| Chỉ chữ cái, số, underscore |
| Chưa tồn tại trong hệ thống |

---

### POST /api/v1/auth/update-avatar
**Cập nhật avatar**

**Input:**
```json
{
  "avatar_url": "https://res.cloudinary.com/xxx/avatar.jpg"
}
```

> **Lưu ý**: Upload ảnh lên Cloudinary trước, sau đó gửi URL

---

### PUT /api/v1/auth/update-profile
**Cập nhật profile (username + avatar)**

**Input:**
```json
{
  "username": "NewUsername",
  "avatar_url": "https://res.cloudinary.com/xxx/avatar.jpg"
}
```

---

### POST /api/v1/auth/change-password
**Đổi mật khẩu**

**Input:**
```json
{
  "old_password": "OldPass123",
  "new_password": "NewPass456",
  "confirm_password": "NewPass456"
}
```

| Validation |
|------------|
| Mật khẩu mới: 8+ ký tự, 1 chữ hoa, 1 số |
| `confirm_password` phải khớp |

---

## 🔧 Admin - Quản lý bài viết

### GET /api/v1/admin/posts
**Lấy danh sách bài viết (Admin)**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query params:**
- `status`: Filter theo `Approved`, `Pending`, `Blocked`
- `limit`: Số lượng (default=50, max=200)

**Output** (Có thêm thông tin user cho Admin):
```json
[
  {
    "_id": "66f123...",
    "content": "...",
    "user_id": "66f456...",
    "username": "SoulSky_1234",
    "user_email": "user@example.com",
    "author_display": "Ẩn danh",
    "is_anonymous": true,
    "moderation_status": "Pending"
  }
]
```

> **Quan trọng**: Admin luôn thấy `username` thật, mặc dù bài viết là ẩn danh

---

### DELETE /api/v1/admin/posts/{post_id}?reason=...
**Xóa bài viết**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query:**
- `reason` (required): Lý do xóa

**Side effects:**
- Xóa bài viết
- Gửi notification đến user: *"Bài viết của bạn đã bị xóa bởi Admin. Lý do: {reason}"*

---

## 💬 Admin - Quản lý comments

### GET /api/v1/admin/comments
**Lấy danh sách comments**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query params:**
- `post_id`: Filter theo bài viết
- `status`: Filter theo `Approved`, `Pending`, `Blocked`
- `limit`: Số lượng (default=50, max=200)

---

### DELETE /api/v1/admin/comments/{comment_id}?reason=...
**Xóa comment**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Side effects:**
- Xóa comment
- Giảm `comment_count` của bài viết
- Gửi notification đến user: *"Bình luận của bạn đã bị xóa bởi Admin. Lý do: {reason}"*

---

## 🚩 Admin - Reports

### GET /api/v1/admin/reports
**Lấy danh sách báo cáo**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query:**
- `status`: `pending`, `resolved`, `dismissed`

---

### PUT /api/v1/admin/reports/{report_id}/resolve?action=...
**Xử lý báo cáo**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query:**
- `action`: `delete_content`, `warn_user`, `dismiss`

---

## 📰 Admin - Expert Articles

### GET /api/v1/admin/expert-articles/pending
**Lấy danh sách bài viết Expert đang chờ duyệt**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

---

### PUT /api/v1/admin/expert-articles/{article_id}/status?status=...
**Duyệt/từ chối bài viết Expert**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Query:**
- `status`: `approved` hoặc `rejected`

**Side effects:**
- Cập nhật status bài viết
- Gửi notification đến Expert

---

## 📊 Admin - Thống kê

### GET /api/v1/admin/stats
**Thống kê tổng quan hệ thống**

| Yêu cầu | |
|---------|--|
| Auth | ✅ Bearer Token |
| Role | admin |

**Output:**
```json
{
  "users": {
    "total": 1500,
    "experts": 25
  },
  "posts": {
    "total": 5000,
    "pending": 50,
    "blocked": 30
  },
  "comments": {
    "total": 12000
  },
  "reports": {
    "pending": 15
  },
  "expert_articles": {
    "pending": 5
  }
}
```

---

## 📌 Tổng hợp APIs

| Feature | API | Method | Auth | Role |
|---------|-----|--------|:----:|------|
| **Đăng bài** | `/anon-posts/` | POST | ✅ | user |
| **Xem bài viết** | `/anon-posts/` | GET | ❌ | - |
| **Bài viết của mình** | `/anon-posts/my-posts` | GET | ✅ | user |
| **Chi tiết bài** | `/anon-posts/{id}` | GET | ❌ | - |
| **Xóa bài** | `/anon-posts/{id}` | DELETE | ✅ | owner |
| **Comment** | `/anon-comments/` | POST | ✅ | user |
| **Xem comments** | `/anon-comments/{post_id}` | GET | ❌ | - |
| **Xóa comment** | `/anon-comments/{id}` | DELETE | ✅ | owner |
| **Like** | `/anon-likes/{post_id}` | POST | ✅ | user |
| **Unlike** | `/anon-likes/{post_id}` | DELETE | ✅ | user |
| **Report** | `/reports/` | POST | ✅ | user |
| **Thông tin user** | `/auth/me` | GET | ✅ | user |
| **Cập nhật username** | `/auth/update-username` | POST | ✅ | user |
| **Cập nhật avatar** | `/auth/update-avatar` | POST | ✅ | user |
| **Cập nhật profile** | `/auth/update-profile` | PUT | ✅ | user |
| **Đổi mật khẩu** | `/auth/change-password` | POST | ✅ | user |
| **[Admin] Xem posts** | `/admin/posts` | GET | ✅ | admin |
| **[Admin] Xóa post** | `/admin/posts/{id}` | DELETE | ✅ | admin |
| **[Admin] Xem comments** | `/admin/comments` | GET | ✅ | admin |
| **[Admin] Xóa comment** | `/admin/comments/{id}` | DELETE | ✅ | admin |
| **[Admin] Reports** | `/admin/reports` | GET | ✅ | admin |
| **[Admin] Xử lý report** | `/admin/reports/{id}/resolve` | PUT | ✅ | admin |
| **[Admin] Expert articles** | `/admin/expert-articles/pending` | GET | ✅ | admin |
| **[Admin] Duyệt article** | `/admin/expert-articles/{id}/status` | PUT | ✅ | admin |
| **[Admin] Thống kê** | `/admin/stats` | GET | ✅ | admin |

---

*Tài liệu được tạo: December 7, 2025*
