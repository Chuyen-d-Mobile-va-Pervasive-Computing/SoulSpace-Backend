# SoulSpace Backend API Reference

Base URL: `/api/v1`

Authentication:
- User/Admin/Expert endpoints (trừ các endpoint “Public”) dùng JWT Bearer trong header `Authorization: Bearer <token>`.
- Vai trò (role) được kiểm tra ở backend: `user`, `admin`, `expert`.

## Common – Authentication
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/auth/register` | POST | Public | `email`, `password`, `username` | Đăng ký user |
| `/auth/login` | POST | Public | `email`, `password` | Đăng nhập, trả `access_token` |
| `/auth/forgot-password` | POST | Public | `email` | Gửi OTP qua email |
| `/auth/reset-password` | POST | Public | `email`, `otp`, `new_password` | Đặt lại mật khẩu |
| `/auth/change-password` | POST | Bearer | `old_password`, `new_password` | Đổi mật khẩu |
| `/auth/update-username` | POST | Bearer | `username` | Đổi username |
| `/auth/update-avatar` | POST | Bearer | `avatar_url` | Cập nhật avatar (URL đã upload) |
| `/auth/update-profile` | PUT | Bearer | `username?`, `avatar_url?` | Cập nhật profile |
| `/auth/me` | GET | Bearer | - | Thông tin user hiện tại |

## Upload (Cloudinary)
| Endpoint | Method | Auth | Input | Mô tả |
| --- | --- | --- | --- | --- |
| `/upload/public/avatar` | POST | Public | `file` (image) | Upload avatar công khai |
| `/upload/public/certificate` | POST | Public | `file` (pdf/png/jpg) | Upload chứng chỉ |
| `/upload/public/post-image` | POST | Public | `file` (image) | Upload ảnh bài viết (public) |
| `/upload/user/avatar` | POST | Bearer | `file` (image) | Upload avatar user |
| `/upload/user/post-image` | POST | Bearer | `file` (image) | Upload ảnh bài viết user |
| `/upload/expert/avatar` | POST | Bearer | `file` (image) | Upload avatar expert |
| `/upload/expert/certificate` | POST | Bearer | `file` (pdf/png/jpg) | Upload chứng chỉ expert |
| `/upload/expert/article-image` | POST | Bearer | `file` (image) | Upload ảnh bài viết chuyên gia |
| `/upload/admin/test-image` | POST | Bearer | `file` (image) | Upload ảnh phục vụ test admin |

Phản hồi chung: `{url, public_id, format, width?, height?, size?}`.

## Expert Authentication
| Endpoint | Method | Auth | Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/auth/expert/register` | POST | Public | Thông tin đăng ký (email/password/username) | Đăng ký chuyên gia (phase 1) |
| `/auth/expert/complete-profile` | POST | Public | Hồ sơ chuyên gia (họ tên, avatar_url, certificate_url, bio, ...) | Hoàn tất hồ sơ (phase 2) |
| `/auth/expert/login` | POST | Public | `email`, `password` | Đăng nhập (cần status `approved`) |

## User – Bài viết ẩn danh
### Posts
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/anon-posts/` | POST | Bearer | `content` (req), `is_anonymous?` (bool), `hashtags?` (list), `image_url?` | Tạo bài với URL ảnh sẵn |
| `/anon-posts/with-image` | POST (multipart) | Bearer | Fields: `content`, `is_anonymous`, `hashtags` (csv), `image?` | Tạo bài và upload ảnh |
| `/anon-posts/` | GET | Optional | Query: `limit` | Danh sách bài đã duyệt; nếu có token, trả thêm `is_liked`, `is_owner` |
| `/anon-posts/my-posts` | GET | Bearer | Query: `limit` | Bài của chính user (kể cả Pending/Blocked) |
| `/anon-posts/{post_id}` | GET | Optional | Path: `post_id` | Chi tiết bài; nếu có token, kèm trạng thái like/owner |
| `/anon-posts/{post_id}` | DELETE | Bearer | Path: `post_id` | Xóa bài của mình |

### Comments
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/anon-comments/` | POST | Bearer | `post_id`, `content`, `is_preset?` | Tạo bình luận |
| `/anon-comments/{post_id}` | GET | Public | Path: `post_id` | Danh sách comment của post |
| `/anon-comments/{comment_id}` | DELETE | Bearer | Path: `comment_id` | Xóa comment của mình |

### Likes
| Endpoint | Method | Auth | Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/anon-likes/{post_id}` | POST | Bearer | Path: `post_id` | Thích bài |
| `/anon-likes/{post_id}` | DELETE | Bearer | Path: `post_id` | Bỏ thích |

## User – Journal
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/journal/` | POST (multipart) | Bearer | Fields: `text_content` (req), `tags` (JSON string list), `audio?` (.mp3/.m4a), `emotion_label?` | Tạo journal, auto tưới cây nếu sentiment tích cực |
| `/journal/` | GET | Bearer | - | Danh sách journal của user |
| `/journal/test-stt` | POST (multipart) | Public | `voice_note` (mp3) | Test STT, trả text và thời gian xử lý |

## User – Reminders
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/reminders/` | GET | Bearer | - | Danh sách nhắc nhở |
| `/reminders/` | POST | Bearer | `title`, `repeat_type` (`once/daily/custom`), `time_of_day` (`HH:MM`), `repeat_days?`, `notes?` | Tạo nhắc nhở |
| `/reminders/{id}` | PUT | Bearer | Body: như trên (cập nhật), Path: `id` | Cập nhật & reschedule |
| `/reminders/{id}` | DELETE | Bearer | Path: `id` | Xóa nhắc nhở |
| `/reminders/toggle/{id}` | POST | Bearer | `is_active` | Bật/tắt nhắc nhở |

## User – Games & Điểm
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/game/choose/questions` | GET | Public | - | Câu hỏi minigame Choose |
| `/game/match/pairs` | GET | Public | - | Cặp từ minigame Match |
| `/game/crossword/words` | GET | Public | - | Từ vựng minigame Crossword |
| `/game/complete` | POST | Bearer | `game_type`, `score` | Ghi nhận hoàn thành game, cộng điểm, trả `earned_points`, `total_points`, `new_badges` |
| `/game/user/{user_id}/points` | GET | Bearer (owner) | Path: `user_id` | Điểm tổng của user |

## User – Badges
| Endpoint | Method | Auth | Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/badges/user/{user_id}` | GET | Bearer (owner) | Path: `user_id` | Badges đã mở khóa |
| `/badges/user/{user_id}/all` | GET | Bearer (owner) | Path: `user_id` | Tất cả badges (earned + locked) |

## User – Tests (trắc nghiệm)
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/tests` | GET | Public | - | Danh sách test |
| `/tests/{test_code}/questions` | GET | Public | Path: `test_code` | Câu hỏi test |
| `/tests/{test_code}/submit` | POST | Bearer | `answers` (dict) | Nộp bài |
| `/tests/result/{result_id}` | GET | Bearer | Path: `result_id` | Kết quả test |

## User – Mental Tree
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/tree/status` | GET | Bearer | - | Trạng thái cây |
| `/tree/nourish` | POST | Bearer | `action_id`, `positive_thoughts` | Tưới cây bằng hành động tích cực |
| `/tree/positive-actions` | GET | Public | - | Danh sách hành động tích cực mẫu |

## User – Reports
| Endpoint | Method | Auth | Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/reports/` | POST | Bearer | `target_id`, `target_type`, `reason` | Báo cáo nội dung |

## Expert (role expert)
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/expert/health` | GET | Bearer | - | Health check |
| `/expert/info` | GET | Bearer (expert) | - | Thông tin expert hiện tại |
| `/expert/my-profile` | GET | Bearer (expert) | - | Hồ sơ expert |
| `/expert/articles` | POST | Bearer (expert) | `{title, content, image_url?, hashtags[]}` | Tạo bài với URL ảnh |
| `/expert/articles/with-image` | POST (multipart) | Bearer (expert) | Fields: `title`, `content`, `hashtags` (csv), `image?` | Tạo bài và upload ảnh |
| `/expert/articles` | GET | Bearer (expert) | - | Danh sách bài của expert |

## Public – Bài viết chuyên gia
| Endpoint | Method | Auth | Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/expert-articles/` | GET | Public | Query: `limit` (default 50) | Danh sách bài đã phê duyệt |
| `/expert-articles/{article_id}` | GET | Public | Path: `article_id` | Chi tiết bài đã phê duyệt |

## Admin (role admin)
### Sức khỏe
| Endpoint | Method | Auth | Mô tả |
| --- | --- | --- | --- |
| `/admin/health` | GET | Bearer (admin) | Health check |

### User management
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/users/create` | POST | Admin | `email`, `password`, `username`, `role` (`admin|expert`) | Tạo admin/expert |
| `/admin/users/create-admin` | POST | Admin | `email`, `password`, `username` | Alias tạo admin |
| `/admin/users` | GET | Admin | Query: `role?`, `limit?` | Danh sách user (ẩn mật khẩu) |

### Post moderation
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/posts` | GET | Admin | `status?`, `limit?` | Danh sách bài (kèm username/email) |
| `/admin/posts/pending` | GET | Admin | `limit?` | Bài Pending |
| `/admin/posts/approved` | GET | Admin | `limit?` | Bài Approved |
| `/admin/posts/moderation` | GET | Admin | `status?`, `risk_level?`, `sentiment?`, `skip?`, `limit?` | Danh sách cho moderation |
| `/admin/posts/{post_id}/detail` | GET | Admin | Path: `post_id` | Chi tiết bài + user info + reports + AI |
| `/admin/posts/{post_id}/status` | PUT | Admin | Body: `status` (`Approved|Hidden`), `reason?` | Cập nhật trạng thái |
| `/admin/posts/batch-status` | PUT | Admin | `post_ids[]`, `status`, `reason?` | Cập nhật hàng loạt |
| `/admin/posts/{post_id}` | DELETE | Admin | Path: `post_id`, Query: `reason` | Xóa bài, gửi notification |

### AI integration
| Endpoint | Method | Auth | Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/ai/webhook/analysis-result` | POST | Admin | `post_id`, `sentiment`, `risk_level` | Webhook nhận kết quả AI, tự đổi status |
| `/admin/posts/{post_id}/ai-feedback` | POST | Admin | `is_correct` (bool), `correct_sentiment?`, `correct_risk_level?`, `feedback_note?` | Feedback cho AI |
| `/admin/stats/ai-analysis` | GET | Admin | - | Thống kê sentiment/risk/status |
| `/admin/stats/overview` | GET | Admin | `period?` (`today|week|month|all`), `date?` (YYYY-MM-DD) | Dashboard nâng cao |
| `/admin/stats` | GET | Admin | `period?`, `date?` | Thống kê tổng quan |

### User violation
| Endpoint | Method | Auth | Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/users/{user_id}/violations` | GET | Admin | Path: `user_id` | Lịch sử vi phạm user |

### Comment moderation
| Endpoint | Method | Auth | Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/comments` | GET | Admin | `post_id?`, `status?`, `limit?` | Danh sách comment |
| `/admin/comments/{comment_id}` | DELETE | Admin | Path: `comment_id`, Query: `reason` | Xóa comment, cập nhật counter |

### Reports moderation
| Endpoint | Method | Auth | Params/Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/reports` | GET | Admin | `status?` | Danh sách reports |
| `/admin/reports/{report_id}/resolve` | PUT | Admin | Path: `report_id`, Query: `action` (`delete_content|warn_user|dismiss`) | Xử lý report |

### Expert articles moderation
| Endpoint | Method | Auth | Params/Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/expert-articles/pending` | GET | Admin | - | Bài pending |
| `/admin/expert-articles/approved` | GET | Admin | `limit?` | Bài approved |
| `/admin/expert-articles` | GET | Admin | `status?`, `limit?` | Danh sách bài, filter status |
| `/admin/expert-articles/{article_id}/status` | PUT | Admin | Path: `article_id`, Query: `status=approved|rejected` | Cập nhật trạng thái, gửi thông báo |

### Admin Tests
| Endpoint | Method | Auth | Body/Params | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/tests` | GET | Admin | - | Danh sách test |
| `/admin/tests/{test_id}` | GET | Admin | Path: `test_id` | Chi tiết test |
| `/admin/tests` | POST | Admin | Body: `{test, questions}` | Tạo test |
| `/admin/tests/{test_id}` | PUT | Admin | Body: cập nhật test/questions | Cập nhật |
| `/admin/tests/{test_id}` | DELETE | Admin | Path: `test_id` | Soft delete |

### Admin expert management
| Endpoint | Method | Auth | Params/Body | Mô tả |
| --- | --- | --- | --- | --- |
| `/admin/experts/{profile_id}/approve` | POST | Admin | Path: `profile_id` | Duyệt chuyên gia |
| `/admin/experts/{profile_id}/reject` | POST | Admin | Path: `profile_id`, Query: `reason?` | Từ chối chuyên gia |
| `/admin/experts/all` | GET | Admin | `status?` | Danh sách chuyên gia |
| `/admin/experts/{profile_id}` | GET | Admin | Path: `profile_id` | Chi tiết hồ sơ chuyên gia |

## Notes
- Mặc định mọi path đã bao gồm prefix `/api/v1` (ví dụ: `POST /api/v1/auth/login`).
- Các endpoint có tag “Public” không yêu cầu JWT; còn lại cần token hợp lệ với đúng vai trò.
- Upload endpoints hỗ trợ các định dạng phổ biến (JPG/PNG/WebP/GIF; audio mp3/m4a tùy nơi).

