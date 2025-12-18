from bson import ObjectId
from fastapi import HTTPException

class AnonLikeRepository:
    def __init__(self, db):
        self.collection = db["anon_likes"]
        self.users_collection = db["users"] 
        self.collection.create_index([("post_id", 1), ("user_id", 1)], unique=True)

    async def like(self, post_id: str, user_id: str, created_at):
        data = {
            "post_id": ObjectId(post_id),
            "user_id": ObjectId(user_id),
            "created_at": created_at
        }
        try:
            result = await self.collection.insert_one(data)
            data["_id"] = result.inserted_id
            return data
        except Exception:
            raise HTTPException(status_code=400, detail="Already liked")

    async def unlike(self, post_id: str, user_id: str):
        result = await self.collection.delete_one({
            "post_id": ObjectId(post_id),
            "user_id": ObjectId(user_id)
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Like not found")
        return {"unliked": True}
    
    async def get_users_by_post_id(self, post_id: str):
        """Lấy danh sách user đã like bài viết"""
        pipeline = [
            {"$match": {"post_id": ObjectId(post_id)}},
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "_id": 0,
                "user_id": {"$toString": "$user_id"},
                "username": "$user_info.username",
                "avatar_url": "$user_info.avatar_url",
                "role": "$user_info.role",
                "liked_at": "$created_at"
            }},
            {"$sort": {"liked_at": -1}}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(length=100)