from apscheduler.schedulers.background import BackgroundScheduler
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import pytz

MONGO_URI = "mongodb+srv://soulspace_user:WCXtXES9Hz4Xb2mA@soulspace-cluster.4ho75yb.mongodb.net/?retryWrites=true&w=majority&appName=soulspace-cluster"
DB_NAME = "soulspace"

# Hàm cập nhật status từ 'upcoming' sang 'past'
def update_past_appointments():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    now = datetime.utcnow()
    # Chuyển status nếu appointment_date < hôm nay hoặc (appointment_date == hôm nay và end_time < giờ hiện tại)
    # Giả sử end_time là chuỗi 'HH:MM'
    today_str = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    # Update cho các lịch đã qua ngày
    result1 = db.appointments.update_many(
        {"status": "upcoming", "appointment_date": {"$lt": today_str}},
        {"$set": {"status": "past", "updated_at": now}}
    )
    # Update cho các lịch hôm nay nhưng đã qua giờ kết thúc
    result2 = db.appointments.update_many(
        {"status": "upcoming", "appointment_date": today_str, "end_time": {"$lt": current_time}},
        {"$set": {"status": "past", "updated_at": now}}
    )
    print(f"Appointments updated to past: {result1.modified_count + result2.modified_count}")

# Khởi tạo scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(update_past_appointments, 'interval', minutes=15)
scheduler.start()

# Nếu chạy độc lập, giữ tiến trình
if __name__ == "__main__":
    import time
    print("Appointment status job started...")
    while True:
        time.sleep(60)
