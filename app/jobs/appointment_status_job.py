from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from datetime import datetime
import pytz
import logging
import time
import signal
import sys

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thông tin kết nối MongoDB
MONGO_URI = "mongodb+srv://soulspace_user:WCXtXES9Hz4Xb2mA@soulspace-cluster.4ho75yb.mongodb.net/?retryWrites=true&w=majority&appName=soulspace-cluster"
DB_NAME = "soulspace"

# Timezone Việt Nam
VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

# Kết nối MongoDB (sync)
client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def normalize_time_string(time_str):
    """
    Chuẩn hóa chuỗi thời gian về định dạng HH:MM (2 chữ số)
    Ví dụ: "9:00" → "09:00", "9:5" → "09:05"
    """
    if not time_str or ':' not in time_str:
        return time_str

    parts = time_str.split(':')
    hour = parts[0].zfill(2)
    minute = parts[1].zfill(2) if len(parts) > 1 else "00"
    return f"{hour}:{minute}"


def cancel_expired_pending_appointments():
    """
    Tự động hủy các lịch hẹn còn ở trạng thái pending nhưng đã qua ngày hẹn.
    Logic: pending + ngày hẹn < hôm nay → cancelled (do hệ thống)
    """
    try:
        now_vn = datetime.now(VIETNAM_TZ)
        today_str = now_vn.strftime("%Y-%m-%d")

        logger.info("Checking expired pending appointments")
        logger.info(f"Current time (VN): {now_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        filter_expired_pending = {
            "status": "pending",
            "appointment_date": {"$lt": today_str}
        }

        count_expired = db.appointments.count_documents(filter_expired_pending)
        logger.info(f"Found {count_expired} expired pending appointments")

        if count_expired > 0:
            samples = list(db.appointments.find(filter_expired_pending).limit(3))
            for idx, apt in enumerate(samples, 1):
                logger.info(f"Sample {idx}: Date={apt.get('appointment_date')}, "
                            f"Time={apt.get('start_time')}-{apt.get('end_time')}")

            result = db.appointments.update_many(
                filter_expired_pending,
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_by": "system",
                        "cancel_reason": "Appointment expired - not confirmed in time",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Auto-cancelled {result.modified_count}/{count_expired} appointments")
        else:
            logger.info("No expired pending appointments found")

        logger.info("Expired pending check completed\n")
        return count_expired

    except Exception as e:
        logger.error(f"Error cancelling expired pending appointments: {str(e)}", exc_info=True)
        return 0


def update_past_appointments():
    """
    Cập nhật trạng thái từ 'upcoming' → 'past' cho các lịch đã kết thúc.
    Xử lý theo giờ Việt Nam với 2 trường hợp:
    - Ngày hẹn đã qua
    - Ngày hẹn hôm nay nhưng đã qua giờ kết thúc (end_time)
    """
    try:
        now_vn = datetime.now(VIETNAM_TZ)
        today_str = now_vn.strftime("%Y-%m-%d")
        current_time = now_vn.strftime("%H:%M")

        logger.info("Starting upcoming to past update")
        logger.info(f"Current time (VN): {now_vn.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Today: {today_str} | Current time: {current_time}")

        # Trường hợp 1: Ngày hẹn đã qua
        filter_past_date = {
            "status": "upcoming",
            "appointment_date": {"$lt": today_str}
        }

        count_past_date = db.appointments.count_documents(filter_past_date)
        logger.info(f"Found {count_past_date} appointments with past dates")

        if count_past_date > 0:
            samples = list(db.appointments.find(filter_past_date).limit(3))
            for idx, apt in enumerate(samples, 1):
                logger.info(f"Sample {idx}: Date={apt.get('appointment_date')}, "
                            f"Time={apt.get('start_time')}-{apt.get('end_time')}, "
                            f"Status={apt.get('status')}")

        result1 = db.appointments.update_many(
            filter_past_date,
            {
                "$set": {
                    "status": "past",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Updated {result1.modified_count}/{count_past_date} appointments (past dates)")

        # Trường hợp 2: Hôm nay nhưng đã qua giờ kết thúc
        filter_today = {
            "status": "upcoming",
            "appointment_date": today_str
        }

        appointments_today = list(db.appointments.find(filter_today))
        logger.info(f"Found {len(appointments_today)} upcoming appointments today")

        ids_to_update = []

        for apt in appointments_today:
            end_time = apt.get('end_time', '')
            normalized_end = normalize_time_string(end_time)

            if normalized_end < current_time:
                ids_to_update.append(apt['_id'])
                logger.info(f"Appointment {apt['_id']}: "
                            f"end_time={end_time} (normalized={normalized_end}) < {current_time} → change to PAST")
            else:
                logger.debug(f"Appointment {apt['_id']}: "
                             f"end_time={end_time} (normalized={normalized_end}) >= {current_time} → still UPCOMING")

        result2_count = 0
        if ids_to_update:
            result2 = db.appointments.update_many(
                {"_id": {"$in": ids_to_update}},
                {
                    "$set": {
                        "status": "past",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            result2_count = result2.modified_count
            logger.info(f"Updated {result2_count}/{len(ids_to_update)} appointments (ended today)")
        else:
            logger.info("No appointments today have ended yet")

        # Tổng kết
        total_updated = result1.modified_count + result2_count
        logger.info(f"SUMMARY: Total {total_updated} appointments updated to 'past'")
        logger.info(f" - From past dates: {result1.modified_count}")
        logger.info(f" - From today (ended): {result2_count}")
        logger.info("Upcoming to past update completed\n")

        return total_updated

    except Exception as e:
        logger.error(f"Error updating appointment status: {str(e)}", exc_info=True)
        return 0


def check_appointments_status():
    """
    Hàm debug: Hiển thị tổng quan trạng thái các lịch hẹn hiện tại
    """
    try:
        now_vn = datetime.now(VIETNAM_TZ)
        today_str = now_vn.strftime("%Y-%m-%d")
        current_time = now_vn.strftime("%H:%M")

        logger.info("\nAppointments Status Overview")
        logger.info(f"Current time: {today_str} {current_time}")

        total = db.appointments.count_documents({})
        pending = db.appointments.count_documents({"status": "pending"})
        upcoming = db.appointments.count_documents({"status": "upcoming"})
        past = db.appointments.count_documents({"status": "past"})
        cancelled = db.appointments.count_documents({"status": "cancelled"})

        logger.info(f"Total appointments: {total}")
        logger.info(f" - Pending: {pending}")
        logger.info(f" - Upcoming: {upcoming}")
        logger.info(f" - Past: {past}")
        logger.info(f" - Cancelled: {cancelled}")

        # Pending quá hạn
        expired_pending = list(db.appointments.find(
            {"status": "pending", "appointment_date": {"$lt": today_str}},
            {"appointment_date": 1, "start_time": 1, "end_time": 1}
        ).limit(5))

        if expired_pending:
            logger.info(f"Expired pending appointments (should be cancelled): {len(expired_pending)}")
            for idx, apt in enumerate(expired_pending, 1):
                logger.info(f" {idx}. Date={apt.get('appointment_date')}, "
                            f"Time={apt.get('start_time')}-{apt.get('end_time')}")
        else:
            logger.info("No expired pending appointments")

        # Upcoming có thể đã qua
        upcoming_list = list(db.appointments.find(
            {"status": "upcoming"},
            {"appointment_date": 1, "start_time": 1, "end_time": 1}
        ).sort("appointment_date", 1).limit(10))

        if upcoming_list:
            logger.info(f"Upcoming appointments (max 10 shown):")
            for idx, apt in enumerate(upcoming_list, 1):
                date = apt.get('appointment_date', 'N/A')
                start = apt.get('start_time', 'N/A')
                end = apt.get('end_time', 'N/A')

                is_past_date = date < today_str
                is_today = date == today_str
                normalized_end = normalize_time_string(end)
                is_past_time = is_today and normalized_end < current_time

                flag = ""
                if is_past_date:
                    flag = " (should be past - date)"
                elif is_past_time:
                    flag = " (should be past - time)"

                logger.info(f" {idx:2d}. {date} {start}-{end}{flag}")
        else:
            logger.info("No upcoming appointments")

        logger.info("Status overview completed\n")

    except Exception as e:
        logger.error(f"Error in status check: {str(e)}")


def run_all_maintenance_tasks():
    """
    Thực hiện toàn bộ các tác vụ bảo trì định kỳ
    """
    logger.info("\nRunning all maintenance tasks")

    cancel_expired_pending_appointments()
    update_past_appointments()
    check_appointments_status()

    logger.info("All maintenance tasks completed\n")


def initialize_scheduler():
    """
    Khởi tạo scheduler và đăng ký các job định kỳ
    """
    scheduler = BackgroundScheduler(timezone=VIETNAM_TZ)

    # Job chính: chạy toàn bộ bảo trì mỗi 15 phút
    scheduler.add_job(
        run_all_maintenance_tasks,
        'interval',
        minutes=15,
        id='maintenance_tasks',
        name='Run all maintenance tasks',
        replace_existing=True,
        max_instances=1
    )

    # Job debug: kiểm tra trạng thái mỗi giờ
    scheduler.add_job(
        check_appointments_status,
        'interval',
        hours=1,
        id='check_status',
        name='Check appointments status (debug)',
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()

    logger.info("\nScheduler started successfully")
    logger.info(f"Timezone: {VIETNAM_TZ}")
    logger.info(f"Database: {DB_NAME}")
    logger.info("Active jobs:")
    for job in scheduler.get_jobs():
        logger.info(f" - {job.name} (ID: {job.id})")
        logger.info(f"   Trigger: {job.trigger}")
        logger.info(f"   Next run: {job.next_run_time}")
    logger.info("Scheduler running in background\n")

    return scheduler


# Khởi động scheduler
scheduler = initialize_scheduler()

# Chạy lần đầu ngay khi khởi động
logger.info("Running initial maintenance check...")
run_all_maintenance_tasks()


# Xử lý tín hiệu dừng chương trình
def signal_handler(sig, frame):
    logger.info("\nShutting down scheduler...")
    scheduler.shutdown(wait=True)
    client.close()
    logger.info("Scheduler stopped successfully")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    logger.info("Appointment maintenance scheduler is running. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        signal_handler(None, None)