# 📚 SoulSpace Backend - Expert & Admin API Documentation

**Tài liệu chuyên biệt cho các API dành riêng cho Expert và Admin**  
**Cập nhật**: December 7, 2025

---

## 📑 Mục lục

1. [Tổng quan hệ thống Role](#-tổng-quan-hệ-thống-role)
2. [Expert Authentication Flow](#-expert-authentication-flow)
3. [Expert APIs](#-expert-apis)
4. [Admin APIs - Quản lý Expert](#-admin-apis---quản-lý-expert)
5. [Admin APIs - Quản lý Bài Test](#-admin-apis---quản-lý-bài-test)
6. [Admin APIs - Quản lý Nội dung](#-admin-apis---quản-lý-nội-dung)
7. [Upload APIs](#-upload-apis)

---

## 🎭 Tổng quan hệ thống Role

### Các vai trò trong hệ thống

| Role | Mô tả | Cách tạo |
|------|-------|----------|
| **user** | Người dùng thông thường | Đăng ký qua `/auth/register` |
| **admin** | Quản trị viên hệ thống | Đăng ký với `role: "admin"` hoặc được cấp quyền |
| **expert** | Chuyên gia tâm lý | Đăng ký qua `/auth/expert/register` + duyệt bởi admin |

### Quy trình Expert Status

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Register   │────►│   Pending   │────►│  Approved   │
│  (Phase 1)  │     │  (Phase 2)  │     │  (Active)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Rejected   │
                    │  (Inactive) │
                    └─────────────┘
```

| Status | Có thể đăng nhập | Mô tả |
|--------|------------------|-------|
| **pending** | ❌ Không | Đang chờ admin duyệt |
| **approved** | ✅ Có | Đã được duyệt, có thể làm việc |
| **rejected** | ❌ Không | Bị từ chối, cần liên hệ admin |

---

## 🔐 Expert Authentication Flow

### Quy trình đăng ký Expert (2 giai đoạn)

```
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 1: ĐĂNG KÝ TÀI KHOẢN                    │
├──────────────────────────────────────────────────────────────────┤
│  POST /auth/expert/register                                      │
│  Input: email, password, confirm_password                        │
│  Output: user_id, email, next_step: "complete-profile"           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    UPLOAD AVATAR & CERTIFICATE                   │
├──────────────────────────────────────────────────────────────────┤
│  POST /api/v1/upload/expert/avatar      (Optional)               │
│  POST /api/v1/upload/expert/certificate (Required)               │
│  → Lấy URL từ Cloudinary                                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 2: HOÀN TẤT HỒ SƠ                       │
├──────────────────────────────────────────────────────────────────┤
│  POST /auth/expert/complete-profile                              │
│  Input: user_id, full_name, phone, date_of_birth, ...            │
│  Output: profile_id, status: "pending"                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       CHỜ ADMIN DUYỆT                            │
├──────────────────────────────────────────────────────────────────┤
│  Admin nhận email thông báo                                      │
│  Admin xem hồ sơ: GET /admin/experts/{profile_id}                │
│  Admin duyệt: POST /admin/experts/{profile_id}/approve           │
│  Hoặc từ chối: POST /admin/experts/{profile_id}/reject           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ĐĂNG NHẬP THÀNH CÔNG                       │
├──────────────────────────────────────────────────────────────────┤
│  POST /auth/expert/login                                         │
│  Chỉ approved expert mới đăng nhập được                          │
│  Output: access_token, expert_status: "approved"                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Expert Authentication APIs

### POST /auth/expert/register
**Mô tả**: Đăng ký tài khoản Expert (Giai đoạn 1)

**Điều kiện**: Không cần đăng nhập

**Input**:
```json
{
  "email": "expert@example.com",
  "password": "Expert@123",
  "confirm_password": "Expert@123"
}
```

**Validation**:
| Field | Yêu cầu |
|-------|---------|
| `email` | Email hợp lệ, chưa tồn tại trong hệ thống |
| `password` | Tối thiểu 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt (@$!%*?&#) |
| `confirm_password` | Phải khớp với password |

**Output Success (201)**:
```json
{
  "message": "Expert account created successfully",
  "user_id": "66f1234567890abcdef12345",
  "email": "expert@example.com",
  "next_step": "complete-profile"
}
```

**Errors**:
| Status | Detail |
|--------|--------|
| 400 | "Email already exists" |
| 400 | "Passwords do not match" |
| 400 | "Password must contain uppercase, lowercase, number and special character" |

---

### POST /auth/expert/complete-profile
**Mô tả**: Hoàn tất hồ sơ chuyên gia (Giai đoạn 2)

**Điều kiện**: Đã có user_id từ Phase 1

**Input**:
```json
{
  "user_id": "66f1234567890abcdef12345",
  "full_name": "Nguyễn Văn An",
  "phone": "0901234567",
  "date_of_birth": "15/06/1990",
  "years_of_experience": 5,
  "clinic_name": "Phòng khám Tâm lý Bình An",
  "clinic_address": "123 Đường Nguyễn Huệ, Quận 1, TP.HCM",
  "bio": "Chuyên gia tâm lý học lâm sàng với 5 năm kinh nghiệm",
  "avatar_url": "https://res.cloudinary.com/xxx/avatar.jpg",
  "certificate_url": "https://res.cloudinary.com/xxx/certificate.pdf"
}
```

**Validation**:
| Field | Yêu cầu |
|-------|---------|
| `user_id` | Bắt buộc, phải tồn tại |
| `full_name` | 3-50 ký tự, chỉ chữ cái (bao gồm tiếng Việt) và khoảng trắng |
| `phone` | 10 chữ số, bắt đầu bằng 0 (VD: 0901234567) |
| `date_of_birth` | Định dạng dd/mm/yyyy, tuổi phải >= 25 |
| `years_of_experience` | Số nguyên 1-50 |
| `clinic_name` | 3-100 ký tự |
| `clinic_address` | 10-200 ký tự |
| `bio` | Tùy chọn, tối đa 200 ký tự |
| `avatar_url` | Tùy chọn, URL Cloudinary |
| `certificate_url` | **Bắt buộc**, URL Cloudinary |

**Output Success (200)**:
```json
{
  "message": "Profile completed successfully. Waiting for admin approval.",
  "profile_id": "66f1234567890abcdef67890",
  "username": "expert_nguyenvanan",
  "status": "pending",
  "estimated_review_time": "24-48 hours"
}
```

**Side Effects**:
- Gửi email thông báo cho Admin
- Cập nhật user.expert_status = "pending"

---

### POST /auth/expert/login
**Mô tả**: Đăng nhập tài khoản Expert

**Điều kiện**: 
- ✅ Expert phải có status = "approved"
- ❌ Chặn nếu status = "pending" hoặc "rejected"

**Input**:
```json
{
  "email": "expert@example.com",
  "password": "Expert@123"
}
```

**Output Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "expert_nguyenvanan",
  "role": "expert",
  "expert_status": "approved",
  "profile_completed": true
}
```

**Errors**:
| Status | Detail | Nguyên nhân |
|--------|--------|-------------|
| 401 | "Invalid credentials" | Sai email hoặc password |
| 403 | "Your expert account is pending approval" | Chưa được duyệt |
| 403 | "Your expert account has been rejected" | Đã bị từ chối |
| 403 | "Please complete your profile first" | Chưa hoàn tất hồ sơ |

---

## 👨‍⚕️ Expert APIs

> **Yêu cầu chung**: Tất cả API dưới đây cần:
> - Header: `Authorization: Bearer <expert_token>`
> - Role: `expert`
> - Status: `approved`

---

### GET /expert/health
**Mô tả**: Kiểm tra trạng thái Expert routes

**Điều kiện**: Không cần auth

**Output**:
```json
{
  "status": "healthy",
  "role": "expert",
  "message": "Expert routes are ready for implementation"
}
```

---

### GET /expert/info
**Mô tả**: Lấy thông tin Expert đang đăng nhập

**Điều kiện**: 
- ✅ Đã đăng nhập với role = "expert"

**Output**:
```json
{
  "message": "Expert access granted",
  "user": "expert_nguyenvanan",
  "role": "expert"
}
```

---

### POST /expert/articles
**Mô tả**: Tạo bài viết chuyên môn (PR Article)

**Điều kiện**: 
- ✅ Role = "expert"
- ✅ Status = "approved"

**Input**:
```json
{
  "title": "5 Cách đối phó với stress hiệu quả",
  "content": "Stress là một phần không thể tránh khỏi trong cuộc sống hiện đại. Dưới đây là 5 phương pháp đã được khoa học chứng minh...",
  "image_url": "https://res.cloudinary.com/xxx/article-cover.jpg"
}
```

**Validation**:
| Field | Yêu cầu |
|-------|---------|
| `title` | Tối thiểu 5 ký tự |
| `content` | Tối thiểu 20 ký tự |
| `image_url` | Tùy chọn |

**Output (201)**:
```json
{
  "_id": "66f1234567890abcdef12345",
  "expert_id": "66f1234567890abcdef11111",
  "title": "5 Cách đối phó với stress hiệu quả",
  "content": "Stress là một phần không thể tránh khỏi...",
  "image_url": "https://res.cloudinary.com/xxx/article-cover.jpg",
  "status": "pending",
  "created_at": "2025-12-07T10:30:00Z",
  "approved_at": null
}
```

**Quy trình sau khi tạo**:
1. Bài viết có status = "pending"
2. Admin xem danh sách bài pending: `GET /admin/expert-articles/pending`
3. Admin duyệt/từ chối: `PUT /admin/expert-articles/{article_id}/status`
4. Expert nhận notification về kết quả

---

### GET /expert/articles
**Mô tả**: Lấy danh sách bài viết của Expert đang đăng nhập

**Điều kiện**: 
- ✅ Role = "expert"

**Output**:
```json
[
  {
    "_id": "66f1234567890abcdef12345",
    "expert_id": "66f1234567890abcdef11111",
    "title": "5 Cách đối phó với stress hiệu quả",
    "content": "...",
    "image_url": "...",
    "status": "approved",
    "created_at": "2025-12-07T10:30:00Z",
    "approved_at": "2025-12-07T15:00:00Z"
  }
]
```

---

## 🔧 Admin APIs - Quản lý Expert

> **Yêu cầu chung**: Tất cả API dưới đây cần:
> - Header: `Authorization: Bearer <admin_token>`
> - Role: `admin`

---

### GET /admin/experts/all
**Mô tả**: Lấy danh sách tất cả Experts

**Điều kiện**: 
- ✅ Role = "admin"

**Query Parameters**:
| Param | Type | Mô tả |
|-------|------|-------|
| `status` | string | Lọc theo status: "pending", "approved", "rejected" |

**Ví dụ**: 
- Lấy tất cả: `GET /admin/experts/all`
- Chỉ pending: `GET /admin/experts/all?status=pending`

**Output**:
```json
{
  "total": 5,
  "experts": [
    {
      "user_id": "66f1234567890abcdef12345",
      "email": "expert@example.com",
      "profile_id": "66f1234567890abcdef67890",
      "full_name": "Nguyễn Văn An",
      "phone": "0901234567",
      "date_of_birth": "15/06/1990",
      "years_of_experience": 5,
      "clinic_name": "Phòng khám Tâm lý Bình An",
      "clinic_address": "123 Đường Nguyễn Huệ, Quận 1, TP.HCM",
      "certificate_url": "https://cloudinary.com/certificate.pdf",
      "avatar_url": "https://cloudinary.com/avatar.jpg",
      "bio": "Chuyên gia tâm lý học lâm sàng",
      "status": "pending",
      "created_at": "2025-12-07T10:30:00Z",
      "updated_at": "2025-12-07T10:30:00Z",
      "approval_date": null
    }
  ]
}
```

---

### GET /admin/experts/{profile_id}
**Mô tả**: Xem chi tiết một Expert

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ profile_id tồn tại

**Output**:
```json
{
  "user_id": "66f1234567890abcdef12345",
  "email": "expert@example.com",
  "profile_id": "66f1234567890abcdef67890",
  "full_name": "Nguyễn Văn An",
  "phone": "0901234567",
  "date_of_birth": "15/06/1990",
  "bio": "Chuyên gia tâm lý học lâm sàng",
  "avatar_url": "https://cloudinary.com/avatar.jpg",
  "years_of_experience": 5,
  "clinic_name": "Phòng khám Tâm lý Bình An",
  "clinic_address": "123 Đường Nguyễn Huệ, Quận 1, TP.HCM",
  "certificate_url": "https://cloudinary.com/certificate.pdf",
  "status": "pending",
  "created_at": "2025-12-07T10:30:00Z",
  "updated_at": "2025-12-07T10:30:00Z",
  "approval_date": null,
  "approved_by": null,
  "rejection_reason": null
}
```

---

### POST /admin/experts/{profile_id}/approve
**Mô tả**: Duyệt Expert (chuyển từ pending → approved)

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ Expert status = "pending"

**Side Effects**:
- Cập nhật ExpertProfile.status = "approved"
- Cập nhật User.expert_status = "approved"
- Lưu approval_date và approved_by
- Gửi email thông báo cho Expert

**Output**:
```json
{
  "message": "Expert approved successfully",
  "profile_id": "66f1234567890abcdef67890",
  "expert_email": "expert@example.com",
  "expert_name": "Nguyễn Văn An"
}
```

**Errors**:
| Status | Detail |
|--------|--------|
| 404 | "Expert profile not found" |
| 400 | "Expert is not in pending status" |

---

### POST /admin/experts/{profile_id}/reject
**Mô tả**: Từ chối Expert (chuyển từ pending → rejected)

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ Expert status = "pending"

**Query Parameters**:
| Param | Type | Mô tả |
|-------|------|-------|
| `reason` | string | Lý do từ chối (tùy chọn) |

**Ví dụ**: `POST /admin/experts/{profile_id}/reject?reason=Chứng chỉ không hợp lệ`

**Side Effects**:
- Cập nhật ExpertProfile.status = "rejected"
- Cập nhật User.expert_status = "rejected"
- Lưu rejection_reason
- Gửi email thông báo cho Expert

**Output**:
```json
{
  "message": "Expert rejected",
  "profile_id": "66f1234567890abcdef67890",
  "expert_email": "expert@example.com",
  "reason": "Chứng chỉ không hợp lệ"
}
```

---

## 📋 Admin APIs - Quản lý Bài Test

> **Yêu cầu chung**: 
> - Header: `Authorization: Bearer <admin_token>`
> - Role: `admin`

---

### GET /admin/tests
**Mô tả**: Lấy danh sách tất cả bài test (không bao gồm đã xóa)

**Điều kiện**: 
- ✅ Role = "admin"

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "test_code": "PHQ9",
    "title": "Patient Health Questionnaire-9",
    "description": "Bài test đánh giá mức độ trầm cảm",
    "image_url": "https://cloudinary.com/test-image.jpg",
    "severe_threshold": 20,
    "expert_recommendation": "Nên tìm đến chuyên gia nếu điểm >= 20",
    "num_questions": 9,
    "created_at": "2025-12-07T10:30:00Z",
    "updated_at": null,
    "created_by": "admin_user_id",
    "updated_by": null,
    "is_deleted": false
  }
]
```

---

### GET /admin/tests/{test_id}
**Mô tả**: Xem chi tiết một bài test với danh sách câu hỏi

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ test_id tồn tại và is_deleted = false

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "test_code": "PHQ9",
  "title": "Patient Health Questionnaire-9",
  "description": "Bài test đánh giá mức độ trầm cảm",
  "questions": [
    {
      "id": "66f1234567890abcdef11111",
      "question_text": "Bạn có thường xuyên cảm thấy buồn không?",
      "question_order": 1,
      "options": [
        {
          "option_id": "opt1",
          "option_text": "Không bao giờ",
          "score": 0,
          "option_order": 1
        },
        {
          "option_id": "opt2",
          "option_text": "Thỉnh thoảng",
          "score": 1,
          "option_order": 2
        }
      ]
    }
  ]
}
```

---

### POST /admin/tests
**Mô tả**: Tạo bài test mới với câu hỏi

**Điều kiện**: 
- ✅ Role = "admin"

**Input**:
```json
{
  "test": {
    "test_code": "GAD7",
    "title": "Generalized Anxiety Disorder 7-item",
    "description": "Bài test đánh giá mức độ lo âu",
    "severe_threshold": 15,
    "expert_recommendation": "Nên tìm đến chuyên gia nếu điểm >= 15",
    "image_url": "https://cloudinary.com/gad7.jpg"
  },
  "questions": [
    {
      "question_text": "Bạn có cảm thấy lo lắng hoặc căng thẳng không?",
      "question_order": 1,
      "options": [
        {"option_text": "Không bao giờ", "score": 0, "option_order": 1},
        {"option_text": "Vài ngày", "score": 1, "option_order": 2},
        {"option_text": "Hơn nửa số ngày", "score": 2, "option_order": 3},
        {"option_text": "Gần như mỗi ngày", "score": 3, "option_order": 4}
      ]
    }
  ]
}
```

**Side Effects**:
- Gán created_at = thời điểm hiện tại
- Gán created_by = admin user_id

**Output (201)**:
```json
{
  "test_id": "66f1234567890abcdef99999",
  "message": "Test created successfully"
}
```

---

### PUT /admin/tests/{test_id}
**Mô tả**: Cập nhật thông tin bài test

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ test_id tồn tại

**Input**:
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "severe_threshold": 18
}
```

**Side Effects**:
- Gán updated_at = thời điểm hiện tại
- Gán updated_by = admin user_id

**Output**:
```json
{
  "message": "Test updated successfully"
}
```

---

### DELETE /admin/tests/{test_id}
**Mô tả**: Xóa mềm bài test (soft delete)

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ test_id tồn tại

**Side Effects**:
- Đánh dấu is_deleted = true
- Bài test sẽ không hiển thị cho user

**Output**:
```json
{
  "message": "Test deleted successfully"
}
```

---

## 🔧 Admin APIs - Quản lý Nội dung

---

### GET /admin/health
**Mô tả**: Kiểm tra trạng thái Admin routes

**Output**:
```json
{
  "status": "healthy",
  "role": "admin"
}
```

---

### GET /admin/posts
**Mô tả**: Lấy tất cả bài viết cộng đồng

**Điều kiện**: 
- ✅ Role = "admin"

**Output**: Danh sách tất cả bài viết (cả Approved, Pending, Blocked)

---

### DELETE /admin/posts/{post_id}
**Mô tả**: Xóa bài viết vi phạm và thông báo cho user

**Điều kiện**: 
- ✅ Role = "admin"

**Query Parameters**:
| Param | Type | Mô tả |
|-------|------|-------|
| `reason` | string | Lý do xóa (bắt buộc) |

**Side Effects**:
- Xóa bài viết
- Gửi notification cho user: "Bài viết của bạn đã bị xóa bởi Admin. Lý do: {reason}"

**Output**:
```json
{
  "message": "Post deleted and user notified"
}
```

---

### GET /admin/reports
**Mô tả**: Lấy danh sách báo cáo vi phạm

**Điều kiện**: 
- ✅ Role = "admin"

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "reporter_id": "66f1234567890abcdef11111",
    "target_id": "66f1234567890abcdef22222",
    "target_type": "post",
    "reason": "Nội dung không phù hợp",
    "status": "pending",
    "created_at": "2025-12-07T10:30:00Z"
  }
]
```

---

### GET /admin/expert-articles/pending
**Mô tả**: Lấy danh sách bài viết Expert đang chờ duyệt

**Điều kiện**: 
- ✅ Role = "admin"

**Output**: Danh sách bài viết có status = "pending"

---

### PUT /admin/expert-articles/{article_id}/status
**Mô tả**: Duyệt hoặc từ chối bài viết Expert

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ status phải là "approved" hoặc "rejected"

**Query Parameters**:
| Param | Type | Mô tả |
|-------|------|-------|
| `status` | string | "approved" hoặc "rejected" |

**Side Effects**:
- Cập nhật bài viết
- Nếu approved: gán approved_at = thời điểm hiện tại
- Gửi notification cho Expert

**Output**: Article object đã cập nhật

---

### GET /admin/stats
**Mô tả**: Lấy thống kê hệ thống

**Điều kiện**: 
- ✅ Role = "admin"

**Output**:
```json
{
  "total_users": 1500,
  "total_posts": 5000,
  "pending_reports": 23
}
```

---

## ☁️ Upload APIs

### POST /api/v1/upload/admin/test-image
**Mô tả**: Admin upload ảnh cho bài test

**Điều kiện**: 
- ✅ Role = "admin"
- ✅ File: PNG hoặc JPEG
- ✅ Kích thước: Tối đa 5MB

**Input**: `file` (multipart/form-data)

**Output**:
```json
{
  "url": "https://res.cloudinary.com/xxx/image/upload/v123/image.jpg",
  "public_id": "test-images/abc123",
  "format": "jpg",
  "width": 800,
  "height": 600,
  "size": 102400
}
```

---

### POST /api/v1/upload/expert/avatar
**Mô tả**: Expert upload ảnh đại diện

**Điều kiện**: 
- ✅ Role = "expert" (có thể chưa approved - dùng trong Phase 2)

**Input**: `file` (multipart/form-data)

**Output**: Giống upload admin

---

### POST /api/v1/upload/expert/certificate
**Mô tả**: Expert upload chứng chỉ

**Điều kiện**: 
- ✅ Role = "expert" (có thể chưa approved - dùng trong Phase 2)
- ✅ File: PDF, PNG, JPEG

**Input**: `file` (multipart/form-data)

**Output**: Giống upload admin

---

## 📌 Bảng tổng hợp quyền truy cập

| Endpoint | User | Expert | Admin |
|----------|:----:|:------:|:-----:|
| `POST /auth/expert/register` | ✅ | ✅ | ✅ |
| `POST /auth/expert/complete-profile` | ❌ | ✅ | ❌ |
| `POST /auth/expert/login` | ❌ | ✅ | ❌ |
| `GET /expert/info` | ❌ | ✅ | ❌ |
| `POST /expert/articles` | ❌ | ✅ | ❌ |
| `GET /expert/articles` | ❌ | ✅ | ❌ |
| `GET /admin/experts/all` | ❌ | ❌ | ✅ |
| `POST /admin/experts/{id}/approve` | ❌ | ❌ | ✅ |
| `POST /admin/experts/{id}/reject` | ❌ | ❌ | ✅ |
| `GET /admin/tests` | ❌ | ❌ | ✅ |
| `POST /admin/tests` | ❌ | ❌ | ✅ |
| `DELETE /admin/posts/{id}` | ❌ | ❌ | ✅ |
| `GET /admin/stats` | ❌ | ❌ | ✅ |

---

*Tài liệu được tạo: December 7, 2025*
