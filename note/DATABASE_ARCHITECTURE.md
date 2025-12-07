# 📊 SoulSpace Backend - Database Architecture

## Tổng quan

Dự án **SoulSpace Backend** sử dụng **MongoDB** làm cơ sở dữ liệu chính, kết hợp với:
- **Motor** - Async MongoDB driver cho Python
- **Pydantic** - Data validation và serialization
- **PyObjectId** - Custom ObjectId handler

---

## 🗄️ Danh sách Collections

### 1. 👤 Users Collection
**Mục đích**: Lưu trữ thông tin người dùng hệ thống.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID người dùng |
| `username` | String | ✅ | - | Tên người dùng |
| `email` | EmailStr | ✅ | - | Email đăng nhập |
| `password` | String | ✅ | - | Mật khẩu (đã hash) |
| `role` | Literal["user", "admin", "expert"] | ❌ | "user" | Vai trò |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo tài khoản |
| `last_login_at` | DateTime | ❌ | null | Lần đăng nhập cuối |
| `total_points` | Int | ❌ | 0 | Tổng điểm tích lũy |
| `reset_otp` | String | ❌ | null | OTP reset mật khẩu |
| `reset_otp_expiry` | DateTime | ❌ | null | Thời hạn OTP |

---

### 2. 📝 Anonymous Posts Collection (AnonPost)
**Mục đích**: Lưu trữ bài viết ẩn danh trong cộng đồng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID bài viết |
| `user_id` | ObjectId | ❌ | null | ID người đăng (null nếu chưa đăng nhập) |
| `content` | String | ✅ | - | Nội dung bài viết (min: 1 ký tự) |
| `is_anonymous` | Boolean | ❌ | true | Ẩn danh hay hiển thị tên |
| `hashtags` | List[String] | ❌ | [] | Danh sách hashtag |
| `created_at` | DateTime | ❌ | now() | Thời điểm đăng |
| `moderation_status` | String | ❌ | "Pending" | Trạng thái kiểm duyệt: Approved, Pending, Blocked, RedirectedToExpert |
| `ai_scan_result` | String | ❌ | null | Kết quả AI scan: Safe, Suspicious, Unsafe |
| `flagged_reason` | String | ❌ | null | Lý do bị flag |
| `like_count` | Int | ❌ | 0 | Số lượt thích |
| `comment_count` | Int | ❌ | 0 | Số bình luận |

---

### 3. 💬 Anonymous Comments Collection (AnonComment)
**Mục đích**: Lưu trữ bình luận trên bài viết ẩn danh.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID bình luận |
| `post_id` | ObjectId | ✅ | - | ID bài viết |
| `user_id` | ObjectId | ✅ | - | ID người bình luận |
| `content` | String | ✅ | - | Nội dung bình luận (min: 1 ký tự) |
| `created_at` | DateTime | ❌ | now() | Thời điểm bình luận |
| `moderation_status` | String | ❌ | "Pending" | Trạng thái: Approved, Pending, Blocked |
| `is_preset` | Boolean | ❌ | false | Là bình luận mẫu hay không |

---

### 4. ❤️ Anonymous Likes Collection (AnonLike)
**Mục đích**: Lưu trữ lượt thích bài viết.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID like |
| `post_id` | ObjectId | ✅ | - | ID bài viết được like |
| `user_id` | ObjectId | ✅ | - | ID người like |
| `created_at` | DateTime | ✅ | - | Thời điểm like |

---

### 5. 📔 Journals Collection
**Mục đích**: Lưu trữ nhật ký cảm xúc cá nhân.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID nhật ký |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |
| `emotion_label` | String | ❌ | null | Nhãn cảm xúc |
| `text_content` | String | ❌ | null | Nội dung văn bản |
| `voice_note_path` | String | ❌ | null | Đường dẫn file ghi âm |
| `voice_text` | String | ❌ | null | Nội dung ghi âm đã chuyển đổi |
| `sentiment_label` | String | ❌ | null | Nhãn phân tích cảm xúc |
| `sentiment_score` | Float | ❌ | null | Điểm cảm xúc |
| `tags` | List[String] | ❌ | [] | Danh sách tags |

---

### 6. ⏰ Reminders Collection
**Mục đích**: Lưu trữ nhắc nhở của người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID nhắc nhở |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `title` | String | ✅ | - | Tiêu đề (max: 30 ký tự) |
| `message` | String | ✅ | - | Nội dung (max: 200 ký tự) |
| `time_of_day` | String | ✅ | - | Giờ nhắc (format: "HH:mm") |
| `repeat_type` | String | ✅ | - | Loại lặp: "once", "daily", "custom" |
| `repeat_days` | List[Int] | ❌ | null | Ngày lặp (0-6), chỉ cho "custom" |
| `is_active` | Boolean | ❌ | true | Đang hoạt động |

---

### 7. 🏅 Badges Collection
**Mục đích**: Lưu trữ danh sách huy hiệu.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID huy hiệu |
| `name` | String | ✅ | - | Tên huy hiệu (max: 50) |
| `description` | String | ✅ | - | Mô tả (max: 200) |
| `icon` | String | ✅ | - | Icon (max: 50) |
| `points_required` | Int | ✅ | - | Điểm yêu cầu (≥0) |
| `challenge_id` | ObjectId | ❌ | null | ID thử thách liên quan |
| `order` | Int | ❌ | 0 | Thứ tự hiển thị |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |

---

### 8. 🎖️ User Badges Collection (UserBadge)
**Mục đích**: Lưu trữ huy hiệu đã đạt được của người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID record |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `badge_id` | ObjectId | ✅ | - | ID huy hiệu |
| `earned_at` | DateTime | ❌ | now() | Thời điểm đạt được |

**Quan hệ**: Bảng trung gian Many-to-Many giữa Users và Badges.

---

### 9. 🌳 User Trees Collection (UserTree)
**Mục đích**: Lưu trữ thông tin cây của người dùng (gamification).

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID cây |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `total_xp` | Int | ❌ | 0 | Tổng XP tích lũy |
| `streak_days` | Int | ❌ | 0 | Số ngày liên tiếp |
| `last_watered_at` | DateTime | ❌ | null | Lần tưới cuối |
| `actions` | List[TreeAction] | ❌ | [] | Danh sách hành động |

**Embedded Document - TreeAction**:
| Field | Type | Mô tả |
|-------|------|-------|
| `tree_action_id` | ObjectId | ID hành động |
| `action_id` | ObjectId | Reference đến PositiveAction |
| `action_date` | DateTime | Thời điểm thực hiện |
| `note` | String | Ghi chú (max: 500) |

---

### 10. 🌟 Positive Actions Collection
**Mục đích**: Lưu trữ danh sách hành động tích cực.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID hành động |
| `action_name` | String | ✅ | - | Tên hành động (max: 100) |
| `description` | String | ✅ | - | Mô tả (max: 500) |

---

### 11. 📋 Tests Collection
**Mục đích**: Lưu trữ các bài test tâm lý.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID test |
| `test_code` | String | ✅ | - | Mã test (max: 50) |
| `test_name` | String | ✅ | - | Tên test (max: 100) |
| `description` | String | ✅ | - | Mô tả (max: 500) |
| `num_questions` | Int | ✅ | - | Số câu hỏi |
| `severe_threshold` | Int | ✅ | - | Ngưỡng nghiêm trọng |
| `self_care_guidance` | String | ✅ | - | Hướng dẫn tự chăm sóc (max: 1000) |
| `expert_recommendation` | String | ✅ | - | Khuyến nghị chuyên gia (max: 1000) |
| `image_url` | String | ❌ | null | URL ảnh minh họa |

---

### 12. ❓ Test Questions Collection
**Mục đích**: Lưu trữ câu hỏi của các bài test.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID câu hỏi |
| `test_id` | ObjectId | ✅ | - | ID test (FK) |
| `question_text` | String | ✅ | - | Nội dung câu hỏi (max: 500) |
| `question_order` | Int | ✅ | - | Thứ tự câu hỏi |
| `options` | List[Option] | ✅ | - | Danh sách lựa chọn |

**Embedded Document - Option**:
| Field | Type | Mô tả |
|-------|------|-------|
| `option_id` | ObjectId | ID option |
| `option_text` | String | Nội dung lựa chọn (max: 200) |
| `score_value` | Int | Điểm của lựa chọn |

---

### 13. 📊 User Test Results Collection
**Mục đích**: Lưu trữ kết quả bài test của người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID kết quả |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `test_id` | ObjectId | ✅ | - | ID test |
| `test_code` | String | ✅ | - | Mã test |
| `status` | String | ❌ | "in-progress" | Trạng thái: "in-progress", "completed" |
| `started_at` | DateTime | ❌ | now() | Thời điểm bắt đầu |
| `completed_at` | DateTime | ❌ | null | Thời điểm hoàn thành |
| `total_score` | Int | ❌ | null | Tổng điểm |
| `severity_level` | String | ❌ | null | Mức độ nghiêm trọng (max: 50) |
| `result_label` | String | ❌ | null | Nhãn kết quả (max: 100) |
| `guidance_notes` | String | ❌ | null | Ghi chú hướng dẫn (max: 1000) |
| `needs_expert` | Boolean | ❌ | null | Cần tư vấn chuyên gia |
| `answers` | List[Answer] | ✅ | - | Danh sách câu trả lời |

**Embedded Document - Answer**:
| Field | Type | Mô tả |
|-------|------|-------|
| `question_id` | ObjectId | ID câu hỏi |
| `option_id` | ObjectId | ID option đã chọn |
| `score_value` | Int | Điểm của câu trả lời |

---

### 14. 🎮 Game Questions Collection
**Mục đích**: Lưu trữ câu hỏi cho game trắc nghiệm.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID câu hỏi |
| `question` | String | ✅ | - | Nội dung câu hỏi (max: 500) |
| `correct_answer` | String | ✅ | - | Đáp án đúng (max: 200) |
| `options` | List[String] | ✅ | - | Các lựa chọn (2-6 items) |
| `meaning` | String | ✅ | - | Ý nghĩa/giải thích (max: 1000) |
| `order` | Int | ❌ | 0 | Thứ tự |
| `is_active` | Boolean | ❌ | true | Đang sử dụng |

---

### 15. 🎲 Game Sessions Collection
**Mục đích**: Lưu trữ phiên chơi game của người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID phiên |
| `user_id` | ObjectId | ✅ | - | ID người dùng |
| `game_type` | String | ✅ | - | Loại game: "choose", "match", "crossword" |
| `score` | Int | ✅ | - | Điểm đạt được (≥0) |
| `created_at` | DateTime | ❌ | now() | Thời điểm chơi |

---

### 16. 🔤 Crossword Words Collection
**Mục đích**: Lưu trữ từ vựng cho game ô chữ.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID từ |
| `word` | String | ✅ | - | Từ vựng (max: 50) |
| `clue` | String | ✅ | - | Gợi ý (max: 500) |
| `order` | Int | ❌ | 0 | Thứ tự |
| `is_active` | Boolean | ❌ | true | Đang sử dụng |

---

### 17. 🔗 Match Pairs Collection
**Mục đích**: Lưu trữ cặp từ-nghĩa cho game nối từ.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID cặp |
| `word` | String | ✅ | - | Từ vựng (max: 100) |
| `meaning` | String | ✅ | - | Nghĩa (max: 200) |
| `order` | Int | ❌ | 0 | Thứ tự |
| `is_active` | Boolean | ❌ | true | Đang sử dụng |

---

### 18. #️⃣ Hashtags Collection
**Mục đích**: Lưu trữ các hashtag được sử dụng trong hệ thống.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID hashtag |
| `name` | String | ✅ | - | Tên hashtag (không bao gồm #) |
| `usage_count` | Int | ❌ | 1 | Số lần sử dụng |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |
| `last_used_at` | DateTime | ❌ | now() | Lần sử dụng cuối |

---

### 19. 👨‍⚕️ Expert Messages Collection
**Mục đích**: Lưu trữ tin nhắn chuyển từ bài viết toxic sang chuyên gia.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID tin nhắn |
| `user_id` | ObjectId | ❌ | null | ID người gửi (null nếu chưa đăng nhập) |
| `expert_id` | ObjectId | ❌ | null | ID chuyên gia được giao |
| `original_content` | String | ✅ | - | Nội dung gốc từ bài viết |
| `detected_keywords` | List[String] | ❌ | [] | Từ khóa phát hiện |
| `flagged_reason` | String | ❌ | "" | Lý do bị flag |
| `ai_scan_result` | String | ❌ | "Unsafe" | Kết quả AI scan |
| `status` | String | ❌ | "pending" | Trạng thái: pending, assigned, in_progress, resolved, closed |
| `expert_response` | String | ❌ | null | Phản hồi từ chuyên gia |
| `responded_at` | DateTime | ❌ | null | Thời điểm phản hồi |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |
| `updated_at` | DateTime | ❌ | now() | Thời điểm cập nhật |

---

### 20. 🚩 Reports Collection
**Mục đích**: Lưu trữ báo cáo vi phạm từ người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID báo cáo |
| `reporter_id` | ObjectId | ✅ | - | ID người báo cáo |
| `target_id` | ObjectId | ✅ | - | ID đối tượng bị báo cáo (Post/Comment) |
| `target_type` | String | ✅ | - | "post" hoặc "comment" |
| `reason` | String | ✅ | - | Lý do báo cáo |
| `status` | String | ❌ | "pending" | "pending", "resolved", "rejected" |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |

---

### 21. 📰 Expert Articles Collection
**Mục đích**: Lưu trữ bài viết chuyên môn/PR của Expert.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID bài viết |
| `expert_id` | ObjectId | ✅ | - | ID chuyên gia |
| `title` | String | ✅ | - | Tiêu đề bài viết |
| `content` | String | ✅ | - | Nội dung |
| `image_url` | String | ❌ | null | Ảnh bìa |
| `status` | String | ❌ | "pending" | "pending", "approved", "rejected" |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |
| `approved_at` | DateTime | ❌ | null | Thời điểm duyệt |

---

### 22. 🔔 Notifications Collection
**Mục đích**: Lưu trữ thông báo cho người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID thông báo |
| `user_id` | ObjectId | ✅ | - | ID người nhận |
| `title` | String | ✅ | - | Tiêu đề thông báo |
| `message` | String | ✅ | - | Nội dung |
| `type` | String | ✅ | - | "system", "alert", "expert_connect" |
| `is_read` | Boolean | ❌ | false | Đã đọc chưa |
| `created_at` | DateTime | ❌ | now() | Thời điểm tạo |

---

### 23. 🚫 Sensitive Keywords Collection
**Mục đích**: Lưu trữ từ khóa nhạy cảm để kiểm duyệt nội dung.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID từ khóa |
| `keyword` | String | ✅ | - | Từ khóa chính |
| `category` | String | ✅ | - | Phân loại: suicidal, violence, harassment, etc. |
| `severity` | String | ✅ | - | "hard" (block ngay) hoặc "soft" (chờ duyệt) |
| `variations` | List[String] | ❌ | [] | Các biến thể của từ khóa |

---

### 24. 📋 Moderation Logs Collection
**Mục đích**: Lưu trữ lịch sử kiểm duyệt nội dung.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID log |
| `content_id` | ObjectId | ✅ | - | ID nội dung (post/comment) |
| `content_type` | String | ✅ | - | "post" hoặc "comment" |
| `user_id` | String | ✅ | - | ID người tạo nội dung |
| `text` | String | ✅ | - | Nội dung gốc |
| `detected_keywords` | List[String] | ❌ | [] | Từ khóa phát hiện được |
| `action` | String | ✅ | - | "Approved", "Pending", "Blocked", "Deleted" |
| `created_at` | DateTime | ❌ | now() | Thời điểm kiểm duyệt |

---

### 25. 🏆 Challenges Collection
**Mục đích**: Lưu trữ danh sách thử thách cho người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID thử thách |
| `name` | String | ✅ | - | Tên thử thách |
| `description` | String | ✅ | - | Mô tả thử thách |
| `points` | Int | ✅ | - | Điểm thưởng khi hoàn thành |
| `required_progress` | Int | ✅ | - | Số lần cần thực hiện |
| `actions` | List[ChallengeAction] | ❌ | [] | Danh sách hành động |

**Embedded Document - ChallengeAction**:
| Field | Type | Mô tả |
|-------|------|-------|
| `action_type` | String | Loại hành động: write_journal, share_post, receive_like |
| `points` | Int | Điểm cho hành động |
| `description` | String | Mô tả hành động |

---

### 26. 🎯 User Challenges Collection
**Mục đích**: Lưu trữ tiến độ thử thách của người dùng.

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `_id` | ObjectId | ✅ | auto | ID record |
| `user_id` | String | ✅ | - | ID người dùng |
| `challenge_id` | ObjectId | ✅ | - | ID thử thách |
| `progress` | Int | ❌ | 0 | Tiến độ hiện tại |
| `earned_points` | Int | ❌ | 0 | Điểm đã kiếm được |
| `badges` | List[EarnedBadge] | ❌ | [] | Huy hiệu đạt được |
| `last_action_at` | DateTime | ❌ | null | Thời điểm hành động cuối |
| `share_count` | Int | ❌ | 0 | Số bài đã chia sẻ |
| `like_count` | Int | ❌ | 0 | Số like nhận được |

**Embedded Document - EarnedBadge**:
| Field | Type | Mô tả |
|-------|------|-------|
| `badge_id` | ObjectId | ID huy hiệu |
| `name` | String | Tên huy hiệu |
| `earned_at` | DateTime | Thời điểm đạt được |

---

## 📐 Sơ đồ quan hệ (Entity Relationships)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USERS (Core Entity)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────┬───────────┼───────────┬─────────────────┐
        │                 │           │           │                 │
        ▼                 ▼           ▼           ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌─────────┐ ┌──────────────┐ ┌─────────┐
│   AnonPost    │ │   Journal     │ │Reminder │ │  UserTree    │ │UserBadge│
│   (1:N)       │ │   (1:N)       │ │ (1:N)   │ │   (1:1)      │ │  (M:N)  │
└───────────────┘ └───────────────┘ └─────────┘ └──────────────┘ └─────────┘
        │                                              │                │
        │                                              │                │
        ▼                                              ▼                ▼
┌───────────────┐                              ┌──────────────┐  ┌─────────┐
│  AnonComment  │                              │PositiveAction│  │  Badge  │
│   (1:N)       │                              │   (N:M)      │  │         │
└───────────────┘                              └──────────────┘  └─────────┘
        │
        ▼
┌───────────────┐
│   AnonLike    │
│   (1:N)       │
└───────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         TESTING SYSTEM                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────┐         ┌────────────────┐         ┌──────────────────┐
│   Test    │ ◄─────► │ TestQuestion   │         │  UserTestResult  │
│           │  (1:N)  │ (with Options) │         │   (User + Test)  │
└───────────┘         └────────────────┘         └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           GAME SYSTEM                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌─────────────┐
│ GameQuestion  │    │ CrosswordWord │    │  MatchPair    │    │ GameSession │
│ (choose game) │    │(crossword game│    │ (match game)  │    │ (tracking)  │
└───────────────┘    └───────────────┘    └───────────────┘    └─────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODERATION SYSTEM                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┐         ┌────────────────┐
│   AnonPost    │ ──────► │ ExpertMessage  │
│ (if toxic)    │         │ (redirected)   │
└───────────────┘         └────────────────┘
        │
        ▼
┌───────────────┐
│   Hashtag     │
│ (extracted)   │
└───────────────┘
```

---

## 🔧 Kết nối Database

```python
# app/core/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client[settings.DATABASE_NAME]
```

**Các collection được truy cập thông qua**:
```python
db["users"]
db["anon_posts"]
db["anon_comments"]
db["anon_likes"]
db["journals"]
db["reminders"]
db["badges"]
db["user_badges"]
db["user_trees"]
db["positive_actions"]
db["tests"]
db["test_questions"]
db["user_test_results"]
db["game_questions"]
db["game_sessions"]
db["crossword_words"]
db["match_pairs"]
db["hashtags"]
db["expert_messages"]
db["reports"]
db["expert_articles"]
db["notifications"]
db["sensitive_keywords"]
db["moderation_logs"]
db["challenges"]
db["user_challenges"]
```

---

## 📌 Ghi chú thiết kế

### 1. **Embedded Documents**
- `TestQuestion.options` - Options được nhúng trực tiếp trong câu hỏi
- `UserTree.actions` - Các hành động được nhúng trong document cây
- `UserTestResult.answers` - Câu trả lời được nhúng trong kết quả test

### 2. **Reference Pattern**
- `user_id` được sử dụng làm foreign key trong hầu hết các collection
- `test_id`, `badge_id`, `post_id` dùng cho quan hệ giữa các entities

### 3. **Soft Delete Pattern**
- Các collection game sử dụng `is_active` thay vì xóa cứng

### 4. **Audit Fields**
- `created_at`, `updated_at`, `last_used_at` để theo dõi lịch sử

### 5. **Content Moderation**
- `moderation_status`, `ai_scan_result`, `flagged_reason` cho hệ thống kiểm duyệt nội dung

---

## 📈 Thống kê

| Metric | Value |
|--------|-------|
| Tổng số Collections | 26 |
| Collections có embedded documents | 5 |
| Collections liên quan đến User | 17 |
| Collections cho Game System | 4 |
| Collections cho Testing System | 3 |
| Collections cho Moderation System | 4 |

---

*Tài liệu được tạo tự động - Cập nhật: December 5, 2025*
