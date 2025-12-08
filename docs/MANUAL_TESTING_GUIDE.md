# 📋 Hướng dẫn Test API Manual

> Hướng dẫn chi tiết cách test API của SoulSpace Backend thông qua Swagger UI

---

## 📌 Mục lục

1. [Yêu cầu](#-yêu-cầu)
2. [Khởi động Server](#-khởi-động-server)
3. [Truy cập Swagger UI](#-truy-cập-swagger-ui)
4. [Quy trình Test Manual](#-quy-trình-test-manual)
5. [Tài khoản Test có sẵn](#-tài-khoản-test-có-sẵn)
6. [Các API Groups](#-các-api-groups)
7. [Ví dụ Test từng nhóm API](#-ví-dụ-test-từng-nhóm-api)
8. [Chạy Test Tự Động](#-chạy-test-tự-động)
9. [Troubleshooting](#-troubleshooting)

---

## 📦 Yêu cầu

- Python 3.10+
- MongoDB đang chạy
- Dependencies đã cài đặt (`pip install -r requirements.txt`)

---

## 🚀 Khởi động Server

```bash
# Di chuyển vào thư mục dự án
cd d:\SE405_SE400\SoulSpace-Backend

# Khởi động server với hot-reload
uvicorn app.main:app --port 8000 --reload
```

**Kết quả mong đợi:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxx] using WatchFiles
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🌐 Truy cập Swagger UI

Mở trình duyệt và truy cập:

```
http://127.0.0.1:8000/docs
```

Swagger UI sẽ hiển thị tất cả các API endpoints có sẵn.

---

## 🔄 Quy trình Test Manual

### Bước 1: Tạo tài khoản User

1. Trong Swagger UI, tìm section **🔐 Auth - Authentication**
2. Chọn **POST /api/v1/auth/register**
3. Click **"Try it out"**
4. Nhập Request body:

```json
{
  "email": "testuser@example.com",
  "password": "Test@123456"
}
```

5. Click **"Execute"**
6. Kiểm tra Response - Status 200 là thành công

### Bước 2: Đăng nhập lấy Token

1. Chọn **POST /api/v1/auth/login**
2. Click **"Try it out"**
3. Nhập:

```json
{
  "email": "testuser@example.com",
  "password": "Test@123456"
}
```

4. Click **"Execute"**
5. **Copy giá trị `access_token`** từ response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "SoulPeace_1234",
  "role": "user"
}
```

### Bước 3: Authorize (⚠️ Rất quan trọng!)

1. Click nút **🔓 Authorize** ở góc trên bên phải của Swagger UI
2. Trong ô "Value", nhập:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   > ⚠️ Lưu ý: Phải có từ `Bearer ` (có dấu cách) trước token!

3. Click **Authorize**
4. Click **Close**

✅ Bây giờ bạn có thể test tất cả API yêu cầu xác thực!

---

## 👥 Tài khoản Test có sẵn

| Role | Email | Password | Ghi chú |
|------|-------|----------|---------|
| **Admin** | `admin@gmail.com` | `Admin@123` | Đã tạo sẵn |
| **User** | _(tự tạo)_ | _(tự đặt)_ | Tạo qua `/auth/register` |
| **Expert** | _(admin tạo)_ | _(admin đặt)_ | Admin tạo qua `/admin/users/create` |

### Tạo tài khoản Admin/Expert (chỉ Admin)

Sau khi đăng nhập với tài khoản Admin, gọi:

```
POST /api/v1/admin/users/create
```

Body:
```json
{
  "email": "newexpert@example.com",
  "password": "Expert@123",
  "username": "DrExpert",
  "role": "expert"
}
```

---

## 📂 Các API Groups

| Icon | Group | Prefix | Mô tả |
|------|-------|--------|-------|
| 🔐 | Auth | `/api/v1/auth/` | Đăng ký, đăng nhập, thông tin user |
| 📔 | Journal | `/api/v1/journal/` | Nhật ký cảm xúc (hỗ trợ audio) |
| 📝 | Posts | `/api/v1/anon-posts/` | Bài viết cộng đồng |
| 💬 | Comments | `/api/v1/anon-comments/` | Bình luận bài viết |
| ❤️ | Likes | `/api/v1/anon-likes/` | Like/Unlike bài viết |
| ⏰ | Reminders | `/api/v1/reminders/` | Nhắc nhở hàng ngày |
| 🧪 | Tests | `/api/v1/tests` | Bài test tâm lý |
| 🌳 | Tree | `/api/v1/tree/` | Cây tinh thần |
| 🚨 | Reports | `/api/v1/reports/` | Báo cáo nội dung vi phạm |
| 🔧 | Admin | `/api/v1/admin/` | Quản trị hệ thống |
| 👨‍⚕️ | Expert | `/api/v1/expert/` | Chuyên gia tâm lý |

---

## 📝 Ví dụ Test từng nhóm API

### 1. 📔 Journal (Nhật ký)

**Tạo nhật ký mới:**
```
POST /api/v1/journal/
Content-Type: multipart/form-data

- text_content: "Hôm nay tôi cảm thấy rất vui vì hoàn thành được nhiều việc"
- emotion_label: "Happy"
```

**Lấy danh sách nhật ký:**
```
GET /api/v1/journal/
```

---

### 2. 📝 Posts (Bài viết cộng đồng)

**Tạo bài viết ẩn danh:**
```json
POST /api/v1/anon-posts/
{
  "content": "Chia sẻ trải nghiệm của tôi về việc vượt qua stress...",
  "is_anonymous": true,
  "hashtags": ["stress", "mentalhealth"]
}
```

**Tạo bài viết công khai (hiển thị username):**
```json
POST /api/v1/anon-posts/
{
  "content": "Tôi muốn chia sẻ với mọi người...",
  "is_anonymous": false,
  "hashtags": ["sharing"]
}
```

---

### 3. ❤️ Likes

**Like bài viết:**
```
POST /api/v1/anon-likes/{post_id}
```

**Unlike bài viết:**
```
DELETE /api/v1/anon-likes/{post_id}
```

---

### 4. 💬 Comments

**Tạo bình luận:**
```json
POST /api/v1/anon-comments/
{
  "post_id": "6936571d9ccd80cf8af2f70e",
  "content": "Cảm ơn bạn đã chia sẻ!",
  "is_preset": false
}
```

**Lấy bình luận của bài viết:**
```
GET /api/v1/anon-comments/{post_id}
```

---

### 5. ⏰ Reminders

**Tạo nhắc nhở hàng ngày:**
```json
POST /api/v1/reminders/
{
  "title": "Thiền buổi sáng",
  "message": "Dành 10 phút để thiền định và thư giãn",
  "time_of_day": "07:00",
  "repeat_type": "daily"
}
```

**Tạo nhắc nhở tùy chỉnh (Thứ 2, 4, 6):**
```json
{
  "title": "Tập yoga",
  "message": "Nhớ tập yoga nhé!",
  "time_of_day": "18:00",
  "repeat_type": "custom",
  "repeat_days": [1, 3, 5]
}
```

---

### 6. 🌳 Tree (Cây tinh thần)

**Xem trạng thái cây:**
```
GET /api/v1/tree/status
```

**Lấy danh sách hành động tích cực:**
```
GET /api/v1/tree/positive-actions
```

**Tưới cây (tăng XP):**
```json
POST /api/v1/tree/nourish
{
  "action_id": "...",
  "positive_thoughts": "Hôm nay tôi đã giúp đỡ một người bạn"
}
```

---

### 7. 🔧 Admin APIs

> ⚠️ Cần đăng nhập với tài khoản Admin!

**Xem thống kê hệ thống:**
```
GET /api/v1/admin/stats
```

**Xem danh sách users:**
```
GET /api/v1/admin/users?limit=10
```

**Xem tất cả bài viết (kể cả ẩn danh):**
```
GET /api/v1/admin/posts?limit=10
```

**Tạo tài khoản Admin/Expert:**
```json
POST /api/v1/admin/users/create
{
  "email": "newadmin@company.com",
  "password": "Admin@123",
  "username": "NewAdmin",
  "role": "admin"
}
```

---

## 🤖 Chạy Test Tự Động

### Test nhanh toàn bộ API:

```bash
# Đảm bảo server đang chạy
python scripts/simple_api_test.py
```

**Kết quả mong đợi:**
```
=== API TEST START (ID: ca9e84ae) ===

--- PHASE 1: AUTH ---
[PASS] Register
[PASS] Login
[PASS] Get Me
...

=== SUMMARY ===
PASSED: 27
FAILED: 0
```

### Tạo tài khoản Admin đầu tiên:

```bash
python scripts/create_first_admin.py
```

### Tạo tài khoản Admin test:

```bash
python scripts/create_test_admin.py
```

---

## 🔧 Troubleshooting

### ❌ Lỗi 401 Unauthorized

**Nguyên nhân:** Token không hợp lệ hoặc chưa authorize.

**Giải pháp:**
1. Kiểm tra đã click **Authorize** chưa
2. Đảm bảo format: `Bearer <token>` (có dấu cách sau "Bearer")
3. Token có thể hết hạn, hãy login lại

---

### ❌ Lỗi 403 Forbidden

**Nguyên nhân:** Không có quyền truy cập (role không đúng).

**Giải pháp:**
- Admin APIs yêu cầu role `admin`
- Expert APIs yêu cầu role `expert`
- Đăng nhập đúng tài khoản có quyền tương ứng

---

### ❌ Lỗi 404 Not Found

**Nguyên nhân:** Resource không tồn tại.

**Giải pháp:**
- Kiểm tra lại ID (post_id, comment_id, etc.)
- Đảm bảo resource đã được tạo trước đó

---

### ❌ Lỗi 422 Validation Error

**Nguyên nhân:** Dữ liệu gửi lên không hợp lệ.

**Giải pháp:**
- Kiểm tra format của request body
- Password phải có ít nhất 8 ký tự, 1 chữ hoa, 1 số
- Kiểm tra các required fields

---

### ❌ Connection Refused

**Nguyên nhân:** Server chưa chạy.

**Giải pháp:**
```bash
uvicorn app.main:app --port 8000 --reload
```

---

## 📚 Tài liệu liên quan

- [API Testing Guide](./API_TESTING_GUIDE.md) - Hướng dẫn chi tiết các API
- [API Test Flow](./API_TEST_FLOW.md) - Luồng test step-by-step

---

> 📅 Cập nhật lần cuối: 2025-12-08
