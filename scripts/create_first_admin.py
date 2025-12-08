"""
Script tạo Admin đầu tiên cho hệ thống.
Chạy một lần khi setup lần đầu.

Usage: python scripts/create_first_admin.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, close_db, get_db
from app.core.security import hash_password
from datetime import datetime


async def create_first_admin():
    """Tạo admin đầu tiên nếu chưa tồn tại."""
    
    print("🔐 SoulSpace - First Admin Setup")
    print("=" * 40)
    
    # Initialize database
    await init_db()
    
    # Get database instance
    db = None
    async for database in get_db():
        db = database
        break
    
    if db is None:
        print("❌ Không thể kết nối database!")
        return
    
    users_collection = db["users"]
    
    # Check if admin already exists
    existing_admin = await users_collection.find_one({"role": "admin"})
    if existing_admin:
        print(f"⚠️  Đã có admin trong hệ thống: {existing_admin.get('email')}")
        print("   Nếu muốn tạo thêm admin, hãy dùng API /admin/users/create-admin")
        await close_db()
        return
    
    # Get admin info from environment or prompt
    admin_email = os.getenv("FIRST_ADMIN_EMAIL", "admin@soulspace.com")
    admin_password = os.getenv("FIRST_ADMIN_PASSWORD", "Admin@123456")
    
    print(f"📧 Email: {admin_email}")
    print(f"🔑 Password: {'*' * len(admin_password)}")
    
    # Validate password
    import re
    if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", admin_password):
        print("❌ Password phải có ít nhất 8 ký tự, 1 chữ hoa và 1 số!")
        await close_db()
        return
    
    # Create admin user
    admin_data = {
        "username": "Admin",
        "email": admin_email,
        "password": hash_password(admin_password),
        "role": "admin",
        "total_points": 0,
        "created_at": datetime.utcnow(),
        "last_login_at": None,
        "reset_otp": None,
        "reset_otp_expiry": None
    }
    
    try:
        result = await users_collection.insert_one(admin_data)
        print(f"\n✅ Tạo admin thành công!")
        print(f"   ID: {result.inserted_id}")
        print(f"   Email: {admin_email}")
        print(f"\n🔒 Lưu ý: Hãy đổi mật khẩu sau khi đăng nhập lần đầu!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(create_first_admin())
