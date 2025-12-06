# Note Function & Prerequisites

## 1. Kiểm duyệt nội dung Toxic (Toxic Content Detection)
- **Yêu cầu**: Cần một API AI (như OpenAI, Perspective API, hoặc mô hình tự train) để đánh giá mức độ toxic chính xác hơn việc chỉ match từ khóa.
- **Hiện tại**: Dự án đang dùng danh sách từ khóa tĩnh (`sensitive_keywords`) trong `AnonPostService`.
- **Hướng giải quyết**: 
    - Tạm thời: Đã tích hợp logic gửi thông báo (Notification) khi phát hiện từ khóa "Blocked" hoặc "Pending".
    - Tương lai: Cần thay thế logic regex bằng việc gọi API AI thực tế.

## 2. Hệ thống Thông báo (Notifications)
- **Yêu cầu**: Gửi thông báo cho User khi bài viết bị xóa hoặc khi cần liên hệ Expert.
- **Hiện tại**: Đã tạo bảng `Notifications` và API lấy thông báo.
- **Lưu ý**: Hiện tại chỉ là In-app Notification (lưu vào DB và user pull về). Nếu muốn Push Notification xuống điện thoại (khi app tắt), cần tích hợp Firebase Cloud Messaging (FCM).

## 3. Duyệt bài Expert (Expert Articles)
- **Yêu cầu**: Expert đăng bài -> Trạng thái "Pending" -> Admin duyệt -> "Approved" (Public).
- **Hiện tại**: Đã tạo bảng `ExpertArticles` và luồng duyệt bài trong `AdminRouter`.
- **Lưu ý**: Cần thêm API Public để User đọc các bài viết đã được duyệt (Hiện tại mới chỉ có API cho Expert và Admin).

## 4. Thống kê (Statistics)
- **Yêu cầu**: Admin xem thống kê.
- **Hiện tại**: Đã có API `/admin/stats` trả về số lượng User, Post, và Pending Reports.
- **Tương lai**: Cần thêm thống kê theo thời gian (daily/monthly) và biểu đồ.

## 5. Phân quyền
- **Hiện tại**: Đã cập nhật User Model có thêm role `expert`.
- **Lưu ý**: Cần đảm bảo khi tạo user mới hoặc update user, role `expert` chỉ được cấp bởi Admin (Logic này cần kiểm tra kỹ trong `AuthService` hoặc `AdminRouter` - hiện tại chưa implement API tạo Expert).
