# app/services/admin/post_service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.repositories.anon_post_repository import AnonPostRepository
from app.repositories.moderation_log_repository import ModerationLogRepository
from app.services.common.notification_service import NotificationService
from app.services.common.email_service import EmailService

class AdminPostService:
    def __init__(self, db):
        self.db = db
        self.post_repo = AnonPostRepository(db)
        self.log_repo = ModerationLogRepository(db)
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    async def delete_post_admin(self, post_id: str, reason: str, admin_id: str):
        """Admin delete post (bypass ownership check)"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Lấy thông tin user để gửi email
        user = await self.db["users"].find_one({"_id": post["user_id"]})
        user_email = user.get("email") if user else None
        username = user.get("username", "User") if user else "User"

        await self.post_repo.delete(post_id)

        # Ghi log
        action_text = f"Deleted by Admin: {reason}" if reason else "Deleted by Admin"
        await self.log_repo.create_log(
            content_id=post_id,
            content_type="post",
            user_id=admin_id,
            text=post.get("content", "")[:200],
            detected_keywords=[],
            action=action_text
        )

        # Gửi thông báo in-app
        await self.notification_service.create_notification(
            user_id=str(post["user_id"]),
            title="Post Deleted",
            message=f"Your post has been deleted by Admin. Reason: {reason}",
            type="alert"
        )

        # Gửi email thông báo xóa bài viết
        if user_email:
            try:
                await self.email_service.send_post_deleted_email(
                    user_email=user_email,
                    username=username,
                    reason=reason
                )
            except Exception as e:
                print(f"[WARNING] Failed to send post deletion email to {user_email}: {e}")

        return {
            "message": "Post deleted and user notified (app + email)",
            "post_id": post_id,
            "deleted_by": admin_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
    

    async def get_top_topics(self) -> list:
        """
        Thống kê Top 10 Topics (Hashtags) được sử dụng nhiều nhất.
        Các topics còn lại gộp vào 'The other topics'.
        """
        pipeline = [
            # 1. Chỉ lấy các bài viết có hashtags (mảng không rỗng)
            {"$match": {"hashtags": {"$exists": True, "$ne": []}}},
            
            # 2. Tách mảng hashtags ra thành từng document riêng lẻ
            {"$unwind": "$hashtags"},
            
            # 3. Chuẩn hóa về chữ thường để gộp "Love" và "love" thành 1
            {"$project": {
                "hashtag_lower": {"$toLower": "$hashtags"}
            }},
            
            # 4. Group by hashtag và đếm số lượng
            {"$group": {
                "_id": "$hashtag_lower",
                "count": {"$sum": 1}
            }},
            
            # 5. Sắp xếp giảm dần theo số lượng
            {"$sort": {"count": -1}}
        ]

        cursor = self.db["anon_posts"].aggregate(pipeline)
        results = await cursor.to_list(length=None)

        final_stats = []
        others_count = 0

        # Xử lý logic Top 10 + Others
        for index, item in enumerate(results):
            if index < 10:
                final_stats.append({
                    "topic": item["_id"], # Hashtag name
                    "count": item["count"]
                })
            else:
                others_count += item["count"]

        # Nếu có các topic khác ngoài top 10, thêm vào cuối
        if others_count > 0:
            final_stats.append({
                "topic": "The other topics",
                "count": others_count
            })

        return final_stats
    
    async def get_top_active_users_clean_posts(self) -> list:
        """Top 3 users có nhiều bài viết Approved nhất"""
        pipeline = [
            # 1. Filter bài clean
            {"$match": {"moderation_status": "Approved"}},
            # 2. Group by User
            {"$group": {
                "_id": "$user_id",
                "count": {"$sum": 1}
            }},
            # 3. Sort giảm dần
            {"$sort": {"count": -1}},
            # 4. Limit 3
            {"$limit": 3},
            # 5. Lookup thông tin User
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            # 6. Unwind user info
            {"$unwind": "$user_info"},
            # 7. Format output
            {"$project": {
                "user_id": {"$toString": "$_id"},
                "username": "$user_info.username",
                "avatar_url": "$user_info.avatar_url",
                "count": 1,
                "activity_type": "Clean Posts"
            }}
        ]
        
        cursor = self.db["anon_posts"].aggregate(pipeline)
        return await cursor.to_list(length=3)

    async def get_top_energetic_users(self) -> list:
        """
        Top 3 users sôi nổi (Tổng Posts + Comments).
        FIX: Sử dụng Batch Query để tránh lỗi event loop trên Python 3.13
        """
        
        # 1. Aggregate Post Counts
        post_counts = await self.db["anon_posts"].aggregate([
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
        ]).to_list(None)
        
        # 2. Aggregate Comment Counts
        comment_counts = await self.db["anon_comments"].aggregate([
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
        ]).to_list(None)
        
        # 3. Merge và Sum count bằng Python
        user_scores = {}
        
        for item in post_counts:
            # Chỉ lấy ID hợp lệ
            if item.get("_id"): 
                uid = str(item["_id"])
                user_scores[uid] = user_scores.get(uid, 0) + item["count"]
            
        for item in comment_counts:
            if item.get("_id"):
                uid = str(item["_id"])
                user_scores[uid] = user_scores.get(uid, 0) + item["count"]
            
        # 4. Sort và lấy Top 3
        sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        
        # 5. Lấy danh sách ID top 3
        top_user_ids = []
        for uid, _ in sorted_users:
            if ObjectId.is_valid(uid):
                top_user_ids.append(ObjectId(uid))
        
        # 6. Fetch thông tin User
        users_cursor = self.db["users"].find(
            {"_id": {"$in": top_user_ids}},
            {"username": 1, "avatar_url": 1}
        )
        users_list = await users_cursor.to_list(length=None)
        
        # Tạo map để tra cứu nhanh: { "user_id_str": user_obj }
        users_map = {str(u["_id"]): u for u in users_list}
        
        # 7. Ghép dữ liệu trả về
        result = []
        for uid, count in sorted_users:
            if uid in users_map:
                user_info = users_map[uid]
                result.append({
                    "user_id": uid,
                    "username": user_info.get("username", "Unknown"),
                    "avatar_url": user_info.get("avatar_url"),
                    "count": count,
                    "activity_type": "Total Interactions"
                })
                
        return result
    
    async def get_post_stats_by_date(self, start_date: str, end_date: str) -> dict:
        """
        Thống kê số lượng bài viết theo từng ngày trong khoảng thời gian.
        start_date, end_date format: YYYY-MM-DD
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            # End date cần +1 ngày để lấy trọn vẹn ngày đó (nếu so sánh datetime)
            # Tuy nhiên với aggregation $dateToString thì có thể filter trước
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Set time to end of day
            end = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        pipeline = [
            # 1. Filter theo range thời gian
            {"$match": {
                "created_at": {"$gte": start, "$lte": end}
            }},
            # 2. Convert created_at sang string YYYY-MM-DD và group
            {"$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            # 3. Sort theo ngày tăng dần
            {"$sort": {"_id": 1}}
        ]

        cursor = self.db["anon_posts"].aggregate(pipeline)
        results = await cursor.to_list(length=None)

        # Format lại dữ liệu
        daily_stats = []
        total_count = 0
        
        for item in results:
            count = item["count"]
            daily_stats.append({
                "date": item["_id"],
                "count": count
            })
            total_count += count

        return {
            "total_in_period": total_count,
            "daily_stats": daily_stats
        }
    