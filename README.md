# SoulSpace Backend

## Giới thiệu
SoulSpace Backend là hệ thống API được xây dựng bằng Python (FastAPI) phục vụ cho ứng dụng SoulSpace, hỗ trợ các chức năng quản lý người dùng, chuyên gia, bài viết, lịch hẹn, trò chơi, báo cáo, và nhiều tính năng khác.

## Cấu trúc thư mục chính
- `app/` - Chứa mã nguồn backend chính, được tổ chức theo mô hình phân tầng:

	```
	app/
	├── main.py                # Điểm khởi tạo FastAPI app
	├── api/                   # Định nghĩa các route (endpoint) chia theo nhóm: user, admin, expert, common...
	├── core/                  # Cấu hình, khởi tạo DB, các thành phần core (config, security, permission...)
	├── jobs/                  # Các tác vụ định kỳ (cron job, background job...)
	├── models/                # Định nghĩa các model (MongoDB document/schema)
	├── repositories/          # Lớp truy xuất dữ liệu (Data Access Layer)
	├── schemas/               # Định nghĩa các schema (Pydantic) cho request/response
	├── services/              # Xử lý logic nghiệp vụ (Business Logic Layer)
	├── tests/                 # Unit test, integration test
	├── utils/                 # Các hàm tiện ích, helper
	└── __pycache__/           # File cache biên dịch Python
	```

	- **api/**: Định nghĩa các route, chia nhỏ theo từng nhóm chức năng (user, admin, expert, common). Mỗi nhóm có thể có nhiều router nhỏ bên trong.
	- **core/**: Cấu hình ứng dụng, khởi tạo database, các thành phần bảo mật, permission, config chung.
	- **jobs/**: Chứa các script chạy định kỳ (ví dụ: cập nhật trạng thái lịch hẹn).
	- **models/**: Định nghĩa các model tương ứng với các collection trong MongoDB.
	- **repositories/**: Lớp truy xuất dữ liệu, thao tác trực tiếp với database.
	- **schemas/**: Định nghĩa các schema (Pydantic) cho dữ liệu vào/ra API.
	- **services/**: Chứa các service xử lý logic nghiệp vụ, tách biệt với tầng truy xuất dữ liệu và API.
	- **tests/**: Chứa các test case cho hệ thống.
	- **utils/**: Các hàm tiện ích dùng chung.

- `Only_Model/` - Chứa các file liên quan đến AI/model
- `docs/` - Tài liệu tham khảo API và hướng dẫn test
- `scripts/` - Các script hỗ trợ kiểm thử, quản trị
- `venv/` - Môi trường ảo Python

## Yêu cầu hệ thống
- Python >= 3.10
- MongoDB Atlas (hoặc MongoDB server)
- pip (Python package manager)

## Hướng dẫn cài đặt môi trường

### 1. Clone source code
```bash
git clone <repo-url>
cd SoulSpace-Backend
```

### 2. Tạo và kích hoạt môi trường ảo
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```


### 4. Cấu hình biến môi trường
- Tạo file `.env` ở thư mục gốc (nếu chưa có)
- Tham khảo các biến môi trường mẫu dưới đây hoặc hỏi quản trị viên để lấy thông tin kết nối MongoDB, cấu hình JWT, email, cloud, ...

Ví dụ nội dung file `.env`:
```env
MONGO_URI=mongodb+srv://<user>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority&appName=<app-name>
DATABASE_NAME=soulspace
JWT_SECRET_KEY=<chuỗi-bất-kỳ-dùng-làm-secret>
ALLOWED_ORIGINS=http://localhost:3000
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=<email-gửi>
EMAIL_PASSWORD=<mật-khẩu-ứng-dụng-email>
SENTIMENT_MODEL=roberta
ASSEMBLYAI_API_KEY=<api-key-của-assemblyai>
CLOUDINARY_CLOUD_NAME=<cloudinary-cloud-name>
CLOUDINARY_API_KEY=<cloudinary-api-key>
CLOUDINARY_API_SECRET=<cloudinary-api-secret>
```

**Giải thích và cách lấy các biến:**
- `MONGO_URI`: Lấy từ MongoDB Atlas (https://cloud.mongodb.com), tạo cluster và user, copy connection string.
- `DATABASE_NAME`: Tên database sử dụng.
- `JWT_SECRET_KEY`: Tự tạo chuỗi random (có thể dùng lệnh Python: `import secrets; print(secrets.token_hex(32))`).
- `ALLOWED_ORIGINS`: Domain frontend được phép truy cập API (ví dụ: http://localhost:3000).
- `EMAIL_HOST`, `EMAIL_PORT`: Thường dùng SMTP của Gmail hoặc dịch vụ email khác.
- `EMAIL_USER`: Email dùng để gửi mail (nên dùng email riêng cho hệ thống).
- `EMAIL_PASSWORD`: Mật khẩu ứng dụng (App password) tạo trong phần bảo mật của Gmail (không dùng mật khẩu đăng nhập thông thường, xem hướng dẫn tại https://support.google.com/accounts/answer/185833?hl=vi).
- `SENTIMENT_MODEL`: Tên model phân tích cảm xúc sử dụng (ví dụ: roberta).
- `ASSEMBLYAI_API_KEY`: Đăng ký tài khoản tại https://www.assemblyai.com/ để lấy API key.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: Đăng ký tài khoản tại https://cloudinary.com/ để lấy thông tin này.

> **Lưu ý bảo mật:** Không commit file `.env` lên git. Thông tin nhạy cảm như mật khẩu, API key chỉ nên chia sẻ nội bộ.

### 5. Chạy server backend
```bash
uvicorn app.main:app --reload
```
- Truy cập API docs tại: http://localhost:8000/docs

### 6. Chạy các job định kỳ (ví dụ cập nhật trạng thái lịch hẹn)
```bash
python app/jobs/appointment_status_job.py
```