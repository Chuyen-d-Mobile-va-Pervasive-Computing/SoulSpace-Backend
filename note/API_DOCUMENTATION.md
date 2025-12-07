# 📚 SoulSpace Backend - API Documentation

**Base URL**: `/api/v1`  
**Cập nhật lần cuối**: December 7, 2025

---

## 📑 Mục lục

1. [🔐 Common - Authentication](#-common---authentication)
2. [🔐 Expert Auth](#-expert-auth)
3. [🔧 Admin Expert Management](#-admin-expert-management)
4. [📋 Admin - Quản lý bài Test](#-admin---quản-lý-bài-test)
5. [📝 User - Làm bài Test](#-user---làm-bài-test)
6. [📔 User - Journal (Nhật ký)](#-user---journal-nhật-ký)
7. [📝 User - Anonymous Posts (Bài viết ẩn danh)](#-user---anonymous-posts-bài-viết-ẩn-danh)
8. [💬 User - Anonymous Comments (Bình luận)](#-user---anonymous-comments-bình-luận)
9. [❤️ User - Anonymous Likes (Thích bài viết)](#️-user---anonymous-likes-thích-bài-viết)
10. [⏰ User - Reminders (Nhắc nhở)](#-user---reminders-nhắc-nhở)
11. [🌳 User - Mental Tree (Cây tinh thần)](#-user---mental-tree-cây-tinh-thần)
12. [🎮 User - Games (Trò chơi)](#-user---games-trò-chơi)
13. [🏅 User - Badges (Huy hiệu)](#-user---badges-huy-hiệu)
14. [🚩 User - Reports (Báo cáo)](#-user---reports-báo-cáo)
15. [👨‍⚕️ Expert - Consultation](#️-expert---consultation)
16. [🔧 Admin - Management](#-admin---management)
17. [☁️ Cloudinary Upload](#️-cloudinary-upload)

---

## 🔐 Common - Authentication

### POST /auth/register
**Mô tả**: Đăng ký tài khoản user/admin mới

**Input**:
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "role": "user"
}
```

**Validation**:
- `password`: Tối thiểu 8 ký tự, có 1 chữ hoa và 1 số
- `role`: "user" hoặc "admin" (mặc định: "user")

**Output**:
```json
{
  "username": "user_abc123",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2025-12-07T10:30:00Z",
  "total_points": 0
}
```

---

### POST /auth/login
**Mô tả**: Đăng nhập tài khoản user/admin

**Input**:
```json
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Output**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "user_abc123",
  "role": "user"
}
```

---

### POST /auth/forgot-password
**Mô tả**: Yêu cầu OTP để reset mật khẩu (gửi qua email)

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Output**:
```json
{
  "message": "OTP sent to email"
}
```

---

### POST /auth/reset-password
**Mô tả**: Reset mật khẩu bằng OTP

**Input**:
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewPassword123"
}
```

**Output**:
```json
{
  "message": "Password reset successfully"
}
```

---

### POST /auth/change-password
**Mô tả**: Đổi mật khẩu (yêu cầu đăng nhập)

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "old_password": "OldPassword123",
  "new_password": "NewPassword456",
  "confirm_password": "NewPassword456"
}
```

**Output**:
```json
{
  "message": "Password changed successfully"
}
```

---

### POST /auth/update-username
**Mô tả**: Cập nhật username (yêu cầu đăng nhập)

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "new_username": "my_new_username"
}
```

**Validation**:
- Chỉ chứa chữ cái, số, và dấu gạch dưới
- Tối thiểu 3 ký tự, tối đa 30 ký tự

**Output**:
```json
{
  "message": "Username updated successfully",
  "username": "my_new_username"
}
```

---

## 🔐 Expert Auth

### POST /auth/expert/register
**Mô tả**: Tạo tài khoản expert, trả về user_id để complete profile (Phase 1)

**Input**:
```json
{
  "email": "expert@example.com",
  "password": "Expert@123",
  "confirm_password": "Expert@123"
}
```

**Validation**:
- `password`: Tối thiểu 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt

**Output**:
```json
{
  "message": "Expert account created successfully",
  "user_id": "66f1234567890abcdef12345",
  "email": "expert@example.com",
  "next_step": "complete-profile"
}
```

---

### POST /auth/expert/complete-profile
**Mô tả**: Hoàn tất hồ sơ expert, tự động chuyển status pending, gửi email thông báo admin (Phase 2)

**Input**:
```json
{
  "user_id": "66f1234567890abcdef12345",
  "full_name": "Nguyễn Văn A",
  "phone": "0901234567",
  "date_of_birth": "15/06/1990",
  "years_of_experience": 5,
  "clinic_name": "Phòng khám Tâm lý ABC",
  "clinic_address": "123 Đường ABC, Quận 1, TP.HCM",
  "bio": "Chuyên gia tâm lý học lâm sàng",
  "avatar_url": "https://cloudinary.com/avatar.jpg",
  "certificate_url": "https://cloudinary.com/certificate.pdf"
}
```

**Validation**:
- `full_name`: 3-50 ký tự, chỉ chữ cái và khoảng trắng
- `phone`: 10 số, bắt đầu bằng 0
- `date_of_birth`: Định dạng dd/mm/yyyy, tuổi >= 25
- `years_of_experience`: 1-50 năm
- `certificate_url`: Bắt buộc

**Output**:
```json
{
  "message": "Profile completed successfully",
  "profile_id": "66f1234567890abcdef67890",
  "username": "expert_abc123",
  "status": "pending",
  "estimated_review_time": "24-48 hours"
}
```

---

### POST /auth/expert/login
**Mô tả**: Đăng nhập expert (chặn pending/rejected, chỉ cho approved qua)

**Input**:
```json
{
  "email": "expert@example.com",
  "password": "Expert@123"
}
```

**Output** (nếu approved):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "expert_abc123",
  "role": "expert",
  "expert_status": "approved",
  "profile_completed": true
}
```

**Error** (nếu pending/rejected):
```json
{
  "detail": "Your expert account is pending approval"
}
```

---

## 🔧 Admin Expert Management

### GET /admin/experts/all?status={pending|approved|rejected}
**Mô tả**: Liệt kê tất cả experts, có thể filter theo status

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Query param `status` (optional): "pending", "approved", "rejected"

**Output**:
```json
{
  "total": 10,
  "experts": [
    {
      "user_id": "66f1234567890abcdef12345",
      "email": "expert@example.com",
      "profile_id": "66f1234567890abcdef67890",
      "full_name": "Nguyễn Văn A",
      "phone": "0901234567",
      "date_of_birth": "15/06/1990",
      "years_of_experience": 5,
      "clinic_name": "Phòng khám Tâm lý ABC",
      "clinic_address": "123 Đường ABC, Quận 1, TP.HCM",
      "certificate_url": "https://cloudinary.com/certificate.pdf",
      "avatar_url": "https://cloudinary.com/avatar.jpg",
      "bio": "Chuyên gia tâm lý",
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
**Mô tả**: Chi tiết đầy đủ 1 expert profile

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Path param `profile_id`

**Output**:
```json
{
  "user_id": "66f1234567890abcdef12345",
  "email": "expert@example.com",
  "profile_id": "66f1234567890abcdef67890",
  "full_name": "Nguyễn Văn A",
  "phone": "0901234567",
  "date_of_birth": "15/06/1990",
  "bio": "Chuyên gia tâm lý",
  "avatar_url": "https://cloudinary.com/avatar.jpg",
  "years_of_experience": 5,
  "clinic_name": "Phòng khám Tâm lý ABC",
  "clinic_address": "123 Đường ABC, Quận 1, TP.HCM",
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
**Mô tả**: Duyệt expert (chỉ pending), cập nhật user.expert_status, gửi email thông báo

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Path param `profile_id`

**Output**:
```json
{
  "message": "Expert approved successfully",
  "profile_id": "66f1234567890abcdef67890",
  "expert_email": "expert@example.com",
  "expert_name": "Nguyễn Văn A"
}
```

---

### POST /admin/experts/{profile_id}/reject?reason=...
**Mô tả**: Từ chối expert (chỉ pending), lưu lý do, cập nhật user.expert_status, gửi email

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: 
- Path param `profile_id`
- Query param `reason` (lý do từ chối)

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

## 📋 Admin - Quản lý bài Test

### POST /admin/tests
**Mô tả**: Tạo mới một bài test với danh sách câu hỏi. Gán trường created_at là thời điểm tạo.

**Headers**: `Authorization: Bearer <admin_token>`

**Input**:
```json
{
  "test": {
    "test_code": "PHQ9",
    "title": "Patient Health Questionnaire-9",
    "description": "Bài test đánh giá mức độ trầm cảm",
    "severe_threshold": 20,
    "expert_recommendation": "Nên tìm đến chuyên gia nếu điểm >= 20",
    "image_url": "https://cloudinary.com/test-image.jpg"
  },
  "questions": [
    {
      "question_text": "Bạn có thường xuyên cảm thấy buồn không?",
      "question_order": 1,
      "options": [
        {"option_text": "Không bao giờ", "score": 0, "option_order": 1},
        {"option_text": "Thỉnh thoảng", "score": 1, "option_order": 2},
        {"option_text": "Thường xuyên", "score": 2, "option_order": 3},
        {"option_text": "Luôn luôn", "score": 3, "option_order": 4}
      ]
    }
  ]
}
```

**Output**:
```json
{
  "test_id": "66f1234567890abcdef12345",
  "message": "Test created successfully"
}
```

---

### GET /admin/tests
**Mô tả**: Lấy danh sách tất cả bài test (filter is_deleted=false), trả về metadata, số câu hỏi, thông tin admin tạo và cập nhật.

**Headers**: `Authorization: Bearer <admin_token>`

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
    "updated_at": "2025-12-07T10:30:00Z",
    "created_by": "admin_user_id",
    "updated_by": null
  }
]
```

---

### GET /admin/tests/{test_id}
**Mô tả**: Trả về chi tiết bài test và danh sách các câu hỏi chưa bị xóa (is_deleted=False). Dùng cho admin xem, quản lý câu hỏi.

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Path param `test_id`

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
        {"option_id": "opt1", "option_text": "Không bao giờ", "score": 0, "option_order": 1}
      ]
    }
  ]
}
```

---

### PUT /admin/tests/{test_id}
**Mô tả**: Cập nhật thông tin một bài test. Gán trường updated_at là thời điểm cập nhật.

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Path param `test_id`
```json
{
  "title": "Updated Test Title",
  "description": "Updated description",
  "severe_threshold": 25
}
```

**Output**:
```json
{
  "message": "Test updated successfully"
}
```

---

### DELETE /admin/tests/{test_id}
**Mô tả**: Xóa mềm (soft delete) một bài test. Đánh dấu is_deleted=True.

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: Path param `test_id`

**Output**:
```json
{
  "message": "Test deleted successfully"
}
```

---

### POST /admin/tests/upload-image
**Mô tả**: Upload ảnh bài test lên Cloudinary, chỉ cho phép PNG/JPEG, dung lượng tối đa 5MB.

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: `file` (multipart/form-data)

**Output**:
```json
{
  "url": "https://res.cloudinary.com/xxx/image/upload/v123/test-image.jpg",
  "public_id": "test-images/abc123",
  "format": "jpg",
  "width": 800,
  "height": 600,
  "size": 102400
}
```

---

## 📝 User - Làm bài Test

### GET /tests
**Mô tả**: Trả về danh sách tất cả các bài test cho user. Chỉ lấy các bài test chưa bị xóa (is_deleted=False). Đếm số lượng câu hỏi chưa bị xóa cho từng test và gán vào trường num_questions.

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "test_code": "PHQ9",
    "title": "Patient Health Questionnaire-9",
    "description": "Bài test đánh giá mức độ trầm cảm",
    "image_url": "https://cloudinary.com/test-image.jpg",
    "num_questions": 9
  }
]
```

---

### GET /tests/{test_code}/questions
**Mô tả**: Trả về danh sách câu hỏi chưa bị xóa của một bài test xác định bằng test_code. Dùng cho màn hình làm bài test.

**Input**: Path param `test_code` (ví dụ: "PHQ9")

**Output**:
```json
{
  "test_code": "PHQ9",
  "title": "Patient Health Questionnaire-9",
  "questions": [
    {
      "id": "66f1234567890abcdef11111",
      "question_text": "Bạn có thường xuyên cảm thấy buồn không?",
      "question_order": 1,
      "options": [
        {"option_id": "opt1", "option_text": "Không bao giờ", "score": 0},
        {"option_id": "opt2", "option_text": "Thỉnh thoảng", "score": 1},
        {"option_id": "opt3", "option_text": "Thường xuyên", "score": 2},
        {"option_id": "opt4", "option_text": "Luôn luôn", "score": 3}
      ]
    }
  ]
}
```

---

### POST /tests/{test_code}/submit
**Mô tả**: Cho phép user nộp kết quả làm bài test. Kiểm tra test còn tồn tại, số câu trả lời phải khớp số câu hỏi. Tính điểm, snapshot lại toàn bộ câu hỏi/đáp án đã chọn. Lưu kết quả vào database.

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `test_code`
```json
{
  "answers": [
    {"question_id": "66f1234567890abcdef11111", "option_id": "opt2"},
    {"question_id": "66f1234567890abcdef22222", "option_id": "opt3"}
  ]
}
```

**Output**:
```json
{
  "result_id": "66f1234567890abcdef99999",
  "total_score": 15,
  "severity_level": "Moderate",
  "result_label": "Trầm cảm mức độ trung bình",
  "needs_expert": true,
  "message": "Test submitted successfully"
}
```

---

### GET /tests/result/{result_id}
**Mô tả**: Trả về chi tiết kết quả làm bài của user. Bao gồm snapshot test, câu hỏi, đáp án đã chọn, tổng điểm, mức độ kết quả, feedback, thời gian hoàn thành.

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `result_id`

**Output**:
```json
{
  "id": "66f1234567890abcdef99999",
  "user_id": "66f1234567890abcdef12345",
  "test_id": "66f1234567890abcdef12345",
  "test_code": "PHQ9",
  "status": "completed",
  "started_at": "2025-12-07T10:30:00Z",
  "completed_at": "2025-12-07T10:45:00Z",
  "total_score": 15,
  "severity_level": "Moderate",
  "result_label": "Trầm cảm mức độ trung bình",
  "guidance_notes": "Bạn nên thực hiện các bài tập thư giãn hàng ngày",
  "needs_expert": true,
  "answers": [
    {
      "question_id": "66f1234567890abcdef11111",
      "option_id": "opt2",
      "score_value": 1
    }
  ]
}
```

---

## 📔 User - Journal (Nhật ký)

### POST /journal/
**Mô tả**: Tạo một nhật ký mới. Hỗ trợ text và audio (speech-to-text).

**Headers**: `Authorization: Bearer <token>`

**Input**: `multipart/form-data`
- `text_content` (string, required): Nội dung văn bản
- `tags` (JSON string, optional): `[{"tag_name": "gratitude"}, {"tag_name": "daily"}]`
- `emotion_label` (string, optional): "Happy", "Sad", "Neutral", etc.
- `audio` (file, optional): File .mp3 hoặc .m4a

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "created_at": "2025-12-07T10:30:00Z",
  "emotion_label": "Happy",
  "text_content": "Hôm nay tôi rất vui...",
  "voice_note_path": null,
  "voice_text": null,
  "sentiment_label": "Positive",
  "sentiment_score": 0.85,
  "tags": ["gratitude", "daily"]
}
```

---

### GET /journal/
**Mô tả**: Lấy tất cả nhật ký của user đang đăng nhập

**Headers**: `Authorization: Bearer <token>`

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "user_id": "66f1234567890abcdef12345",
    "created_at": "2025-12-07T10:30:00Z",
    "emotion_label": "Happy",
    "text_content": "Hôm nay tôi rất vui...",
    "voice_note_path": null,
    "voice_text": null,
    "sentiment_label": "Positive",
    "sentiment_score": 0.85,
    "tags": ["gratitude", "daily"]
  }
]
```

---

### POST /journal/test-stt
**Mô tả**: Test Speech-to-Text với file MP3 tiếng Anh

**Input**: `voice_note` (file .mp3, multipart/form-data)

**Output**:
```json
{
  "voice_text": "Hello, this is a test recording",
  "processing_time": 2.5,
  "status": "success"
}
```

---

## 📝 User - Posts (Bài viết cộng đồng)

> **Lưu ý**: Tính năng này cho phép user đăng bài theo 2 chế độ:
> - `is_anonymous=true`: Đăng ẩn danh (mặc định) - không hiển thị tên
> - `is_anonymous=false`: Đăng bằng tên tài khoản - hiển thị username

### POST /anon-posts/
**Mô tả**: Tạo bài viết mới (ẩn danh hoặc công khai)

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "content": "Hôm nay tôi cảm thấy rất vui vì đã hoàn thành dự án!",
  "is_anonymous": false,
  "hashtags": ["achievement", "happy"]
}
```

**Validation**:
- `content`: 1-5000 ký tự
- `is_anonymous`: true (mặc định) hoặc false
- `hashtags`: Mảng string, tùy chọn

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "content": "Hôm nay tôi cảm thấy rất vui vì đã hoàn thành dự án!",
  "is_anonymous": false,
  "author_name": "john_doe",
  "hashtags": ["achievement", "happy"],
  "created_at": "2025-12-07T10:30:00Z",
  "moderation_status": "Approved",
  "ai_scan_result": "Safe",
  "flagged_reason": null,
  "like_count": 0,
  "comment_count": 0,
  "detected_keywords": [],
  "is_liked": false,
  "is_owner": true
}
```

**Ví dụ đăng ẩn danh**:
```json
{
  "content": "Tôi cảm thấy cô đơn...",
  "is_anonymous": true,
  "hashtags": ["lonely"]
}
```
→ Response sẽ có `author_name: "Ẩn danh"` và `user_id: null`

---

### GET /anon-posts/
**Mô tả**: Lấy danh sách bài viết cộng đồng (đã được duyệt)

**Headers**: `Authorization: Bearer <token>` (optional)

**Query params**:
- `limit` (optional, default=20, max=100): Số lượng bài viết

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "user_id": null,
    "content": "Tôi cảm thấy cô đơn...",
    "is_anonymous": true,
    "author_name": "Ẩn danh",
    "hashtags": ["lonely"],
    "created_at": "2025-12-07T10:30:00Z",
    "moderation_status": "Approved",
    "ai_scan_result": "Safe",
    "flagged_reason": null,
    "like_count": 5,
    "comment_count": 2,
    "detected_keywords": [],
    "is_liked": true,
    "is_owner": false
  },
  {
    "id": "66f1234567890abcdef67890",
    "user_id": "66f1234567890abcdef11111",
    "content": "Hôm nay tôi hoàn thành dự án!",
    "is_anonymous": false,
    "author_name": "john_doe",
    "hashtags": ["achievement"],
    "created_at": "2025-12-07T09:00:00Z",
    "moderation_status": "Approved",
    "ai_scan_result": "Safe",
    "flagged_reason": null,
    "like_count": 10,
    "comment_count": 3,
    "detected_keywords": [],
    "is_liked": false,
    "is_owner": false
  }
]
```

**Giải thích response**:
| Field | Mô tả |
|-------|-------|
| `author_name` | "Ẩn danh" nếu `is_anonymous=true`, username nếu `is_anonymous=false` |
| `user_id` | `null` nếu ẩn danh, ID người đăng nếu không ẩn danh |
| `is_liked` | User hiện tại đã like chưa (cần đăng nhập) |
| `is_owner` | User hiện tại có phải chủ bài viết không |

---

### GET /anon-posts/my-posts
**Mô tả**: Lấy tất cả bài viết của mình (bao gồm Pending, Blocked)

**Headers**: `Authorization: Bearer <token>` (required)

**Query params**:
- `limit` (optional, default=50, max=100): Số lượng bài viết

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "user_id": "66f1234567890abcdef12345",
    "content": "Bài viết đang chờ duyệt...",
    "is_anonymous": true,
    "author_name": "Ẩn danh",
    "hashtags": [],
    "created_at": "2025-12-07T11:00:00Z",
    "moderation_status": "Pending",
    "ai_scan_result": "Suspicious",
    "flagged_reason": "Soft block keyword detected: stress",
    "like_count": 0,
    "comment_count": 0,
    "is_liked": false,
    "is_owner": true
  }
]
```

---

### GET /anon-posts/{post_id}
**Mô tả**: Lấy chi tiết một bài viết

**Headers**: `Authorization: Bearer <token>` (optional)

**Input**: Path param `post_id`

**Output**: Giống response của POST /anon-posts/

---

### DELETE /anon-posts/{post_id}
**Mô tả**: Xóa bài viết của mình (chỉ owner mới có quyền)

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `post_id`

**Output**:
```json
{
  "deleted": true,
  "post_id": "66f1234567890abcdef12345"
}
```

**Error** (không phải owner):
```json
{
  "detail": "You can only delete your own posts"
}
```

---

## 💬 User - Anonymous Comments (Bình luận)

### POST /anon-comments/
**Mô tả**: Tạo bình luận mới trên bài viết

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "post_id": "66f1234567890abcdef12345",
  "content": "Tôi hiểu cảm giác của bạn...",
  "is_preset": false
}
```

**Output**:
```json
{
  "id": "66f1234567890abcdef67890",
  "post_id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "content": "Tôi hiểu cảm giác của bạn...",
  "created_at": "2025-12-07T10:35:00Z",
  "moderation_status": "Pending",
  "is_preset": false
}
```

---

### GET /anon-comments/{post_id}
**Mô tả**: Lấy danh sách bình luận của một bài viết

**Input**: Path param `post_id`

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef67890",
    "post_id": "66f1234567890abcdef12345",
    "user_id": "66f1234567890abcdef12345",
    "content": "Tôi hiểu cảm giác của bạn...",
    "created_at": "2025-12-07T10:35:00Z",
    "moderation_status": "Approved",
    "is_preset": false
  }
]
```

---

### DELETE /anon-comments/{comment_id}
**Mô tả**: Xóa bình luận của mình

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `comment_id`

**Output**:
```json
{
  "message": "Comment deleted successfully"
}
```

---

## ❤️ User - Anonymous Likes (Thích bài viết)

### POST /anon-likes/{post_id}
**Mô tả**: Like một bài viết

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `post_id`

**Output**:
```json
{
  "message": "Post liked successfully",
  "like_count": 6
}
```

---

### DELETE /anon-likes/{post_id}
**Mô tả**: Unlike một bài viết

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `post_id`

**Output**:
```json
{
  "message": "Post unliked successfully",
  "like_count": 5
}
```

---

## ⏰ User - Reminders (Nhắc nhở)

### GET /reminders/
**Mô tả**: Lấy tất cả nhắc nhở của user

**Headers**: `Authorization: Bearer <token>`

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "user_id": "66f1234567890abcdef12345",
    "title": "Uống nước",
    "message": "Nhớ uống đủ 2 lít nước mỗi ngày",
    "time_of_day": "08:00",
    "repeat_type": "daily",
    "repeat_days": null,
    "is_active": true
  }
]
```

---

### POST /reminders/
**Mô tả**: Tạo nhắc nhở mới với lịch tự động

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "title": "Uống nước",
  "message": "Nhớ uống đủ 2 lít nước mỗi ngày",
  "time_of_day": "08:00",
  "repeat_type": "daily",
  "repeat_days": null
}
```

**Validation**:
- `title`: Tối đa 30 ký tự
- `message`: Tối đa 200 ký tự
- `time_of_day`: Định dạng "HH:mm"
- `repeat_type`: "once", "daily", hoặc "custom"
- `repeat_days`: Chỉ dùng khi repeat_type="custom", mảng số 0-6 (0=Chủ nhật)

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "title": "Uống nước",
  "message": "Nhớ uống đủ 2 lít nước mỗi ngày",
  "time_of_day": "08:00",
  "repeat_type": "daily",
  "repeat_days": null,
  "is_active": true
}
```

---

### PUT /reminders/{id}
**Mô tả**: Cập nhật nhắc nhở

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `id` + body giống POST

**Output**: Reminder object đã cập nhật

---

### DELETE /reminders/{id}
**Mô tả**: Xóa nhắc nhở

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `id`

**Output**:
```json
{
  "message": "Reminder deleted successfully"
}
```

---

### POST /reminders/toggle/{id}
**Mô tả**: Bật/tắt trạng thái nhắc nhở

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `id`
```json
{
  "is_active": false
}
```

**Output**:
```json
{
  "message": "Reminder deactivated successfully"
}
```

---

## 🌳 User - Mental Tree (Cây tinh thần)

### GET /tree/status
**Mô tả**: Lấy trạng thái cây tinh thần của user

**Headers**: `Authorization: Bearer <token>`

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "total_xp": 150,
  "streak_days": 7,
  "last_watered_at": "2025-12-07T08:00:00Z",
  "actions": [
    {
      "tree_action_id": "66f1234567890abcdef11111",
      "action_id": "66f1234567890abcdef22222",
      "action_date": "2025-12-07T08:00:00Z",
      "note": "Tôi biết ơn gia đình"
    }
  ]
}
```

---

### POST /tree/nourish
**Mô tả**: Tưới cây bằng hành động tích cực (chỉ 1 lần/ngày)

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "action_id": "66f1234567890abcdef22222",
  "positive_thoughts": "Tôi biết ơn gia đình đã luôn ở bên tôi"
}
```

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "user_id": "66f1234567890abcdef12345",
  "total_xp": 160,
  "streak_days": 8,
  "last_watered_at": "2025-12-08T08:00:00Z",
  "actions": [...]
}
```

**Error** (nếu đã tưới hôm nay):
```json
{
  "detail": "You have already watered the tree today"
}
```

---

### GET /tree/positive-actions
**Mô tả**: Lấy danh sách hành động tích cực mẫu

**Headers**: `Authorization: Bearer <token>`

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef22222",
    "action_name": "Viết 3 điều biết ơn",
    "description": "Ghi lại 3 điều bạn biết ơn trong ngày hôm nay"
  },
  {
    "id": "66f1234567890abcdef33333",
    "action_name": "Thiền 5 phút",
    "description": "Dành 5 phút để thiền và hít thở sâu"
  }
]
```

---

## 🎮 User - Games (Trò chơi)

### GET /game/choose/questions
**Mô tả**: Lấy danh sách câu hỏi cho minigame Choose

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "question": "Khi căng thẳng, bạn nên làm gì?",
    "correct_answer": "Hít thở sâu",
    "options": ["Hít thở sâu", "Tức giận", "Khóc lóc", "Im lặng"],
    "meaning": "Hít thở sâu giúp làm dịu hệ thần kinh và giảm căng thẳng",
    "order": 1
  }
]
```

---

### GET /game/match/pairs
**Mô tả**: Lấy danh sách cặp từ cho minigame Match

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "word": "Anxiety",
    "meaning": "Lo âu",
    "order": 1
  }
]
```

---

### GET /game/crossword/words
**Mô tả**: Lấy từ vựng cho minigame Crossword

**Output**:
```json
[
  {
    "id": "66f1234567890abcdef12345",
    "word": "PEACE",
    "clue": "Trạng thái yên bình, không có xung đột",
    "order": 1
  }
]
```

---

### POST /game/complete
**Mô tả**: ✅ **API CHÍNH** - Xử lý khi user hoàn thành minigame. Lưu session, cộng điểm, check badge mới.

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "game_type": "choose",
  "score": 10
}
```

**Validation**:
- `game_type`: "choose", "match", hoặc "crossword"
- `score`: >= 0

**Output**:
```json
{
  "earned_points": 10,
  "total_points": 50,
  "new_badges": [
    {
      "id": "66f1234567890abcdef12345",
      "name": "PathFinder",
      "description": "Earn 10 points",
      "icon": "pathfinder",
      "points_required": 10
    }
  ]
}
```

---

### GET /game/user/{user_id}/points
**Mô tả**: Lấy tổng điểm của user (chỉ xem được của chính mình)

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `user_id`

**Output**:
```json
{
  "user_id": "66f1234567890abcdef12345",
  "total_points": 50
}
```

---

## 🏅 User - Badges (Huy hiệu)

### GET /badges/user/{user_id}
**Mô tả**: Lấy danh sách badges user đã sở hữu

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `user_id`

**Output**:
```json
[
  {
    "badge_id": "66f1234567890abcdef12345",
    "name": "PathFinder",
    "description": "Earn 10 points",
    "icon": "pathfinder",
    "points_required": 10,
    "earned_at": "2025-12-07T10:30:00Z"
  }
]
```

---

### GET /badges/user/{user_id}/all
**Mô tả**: Lấy tất cả badges (earned + locked) để hiển thị badge system

**Headers**: `Authorization: Bearer <token>`

**Input**: Path param `user_id`

**Output**:
```json
{
  "earned_badges": [
    {
      "badge_id": "66f1234567890abcdef12345",
      "name": "PathFinder",
      "description": "Earn 10 points",
      "icon": "pathfinder",
      "points_required": 10,
      "earned_at": "2025-12-07T10:30:00Z"
    }
  ],
  "locked_badges": [
    {
      "badge_id": "66f1234567890abcdef67890",
      "name": "Tree Master",
      "description": "Reach 100 XP on Mental Tree",
      "icon": "tree_master",
      "points_required": 100
    }
  ],
  "total_earned": 1,
  "total_badges": 6
}
```

---

## 🚩 User - Reports (Báo cáo)

### POST /reports/
**Mô tả**: Báo cáo vi phạm bài viết hoặc bình luận

**Headers**: `Authorization: Bearer <token>`

**Input**:
```json
{
  "target_id": "66f1234567890abcdef12345",
  "target_type": "post",
  "reason": "Nội dung không phù hợp"
}
```

**Validation**:
- `target_type`: "post" hoặc "comment"

**Output**:
```json
{
  "id": "66f1234567890abcdef99999",
  "reporter_id": "66f1234567890abcdef12345",
  "target_id": "66f1234567890abcdef12345",
  "target_type": "post",
  "reason": "Nội dung không phù hợp",
  "status": "pending",
  "created_at": "2025-12-07T10:30:00Z"
}
```

---

## 👨‍⚕️ Expert - Consultation

### GET /expert/health
**Mô tả**: Health check endpoint cho expert routes

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
**Mô tả**: Lấy thông tin expert (yêu cầu role expert)

**Headers**: `Authorization: Bearer <expert_token>`

**Output**:
```json
{
  "message": "Expert access granted",
  "user": "expert_username",
  "role": "expert"
}
```

---

### POST /expert/articles
**Mô tả**: Tạo bài viết chuyên môn/PR

**Headers**: `Authorization: Bearer <expert_token>`

**Input**:
```json
{
  "title": "Cách đối phó với stress",
  "content": "Nội dung bài viết chi tiết...",
  "image_url": "https://cloudinary.com/article-image.jpg"
}
```

**Output**:
```json
{
  "id": "66f1234567890abcdef12345",
  "expert_id": "66f1234567890abcdef12345",
  "title": "Cách đối phó với stress",
  "content": "Nội dung bài viết chi tiết...",
  "image_url": "https://cloudinary.com/article-image.jpg",
  "status": "pending",
  "created_at": "2025-12-07T10:30:00Z",
  "approved_at": null
}
```

---

### GET /expert/articles
**Mô tả**: Lấy danh sách bài viết của expert đang đăng nhập

**Headers**: `Authorization: Bearer <expert_token>`

**Output**: Mảng các bài viết

---

## 🔧 Admin - Management

### GET /admin/health
**Mô tả**: Health check endpoint cho admin routes

**Output**:
```json
{
  "status": "healthy",
  "role": "admin"
}
```

---

### GET /admin/posts
**Mô tả**: Lấy tất cả bài viết (admin)

**Headers**: `Authorization: Bearer <admin_token>`

**Output**: Mảng tất cả bài viết

---

### DELETE /admin/posts/{post_id}?reason=...
**Mô tả**: Xóa bài viết và gửi thông báo cho user

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: 
- Path param `post_id`
- Query param `reason`

**Output**:
```json
{
  "message": "Post deleted and user notified"
}
```

---

### GET /admin/reports
**Mô tả**: Lấy danh sách báo cáo vi phạm

**Headers**: `Authorization: Bearer <admin_token>`

**Output**: Mảng các báo cáo

---

### GET /admin/expert-articles/pending
**Mô tả**: Lấy danh sách bài viết expert đang chờ duyệt

**Headers**: `Authorization: Bearer <admin_token>`

**Output**: Mảng bài viết có status="pending"

---

### PUT /admin/expert-articles/{article_id}/status
**Mô tả**: Duyệt hoặc từ chối bài viết expert

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: 
- Path param `article_id`
- Query param `status`: "approved" hoặc "rejected"

**Output**: Article object đã cập nhật

---

### GET /admin/stats
**Mô tả**: Lấy thống kê hệ thống

**Headers**: `Authorization: Bearer <admin_token>`

**Output**:
```json
{
  "total_users": 1000,
  "total_posts": 5000,
  "pending_reports": 15
}
```

---

## ☁️ Cloudinary Upload

### POST /api/v1/upload/admin/test-image
**Mô tả**: Admin upload ảnh cho bài test

**Headers**: `Authorization: Bearer <admin_token>`

**Input**: `file` (multipart/form-data, PNG/JPEG, max 5MB)

**Output**:
```json
{
  "url": "https://res.cloudinary.com/xxx/image/upload/v123/image.jpg",
  "public_id": "images/abc123",
  "format": "jpg",
  "width": 800,
  "height": 600,
  "size": 102400
}
```

---

### POST /api/v1/upload/expert/avatar
**Mô tả**: Expert upload ảnh đại diện

**Headers**: `Authorization: Bearer <expert_token>`

**Input**: `file` (multipart/form-data)

**Output**:
```json
{
  "url": "https://res.cloudinary.com/xxx/image/upload/v123/avatar.jpg",
  "public_id": "avatars/abc123",
  "format": "jpg",
  "width": 200,
  "height": 200,
  "size": 51200
}
```

---

### POST /api/v1/upload/expert/certificate
**Mô tả**: Expert upload chứng chỉ

**Headers**: `Authorization: Bearer <expert_token>`

**Input**: `file` (multipart/form-data, PDF/PNG/JPEG)

**Output**:
```json
{
  "url": "https://res.cloudinary.com/xxx/image/upload/v123/certificate.pdf",
  "public_id": "certificates/abc123",
  "format": "pdf",
  "size": 204800
}
```

---

## 📌 Ghi chú chung

### Authentication
- Tất cả API có **Headers Required** đều cần: `Authorization: Bearer <access_token>`
- Token lấy từ response của `/auth/login` hoặc `/auth/expert/login`

### Error Responses
```json
{
  "detail": "Error message here"
}
```

Các HTTP Status Code thường gặp:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (chưa đăng nhập)
- `403`: Forbidden (không có quyền)
- `404`: Not Found
- `409`: Conflict (duplicate, already exists)
- `500`: Internal Server Error

---

*Tài liệu được tạo tự động - Cập nhật: December 7, 2025*
