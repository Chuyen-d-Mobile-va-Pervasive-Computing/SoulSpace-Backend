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
            
            # 1. Join bảng Users
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            
            # 2. Xử lý ID để khớp kiểu dữ liệu (ObjectId vs String)
            {"$addFields": {
                # Tạo thêm field ID dạng String để lookup nếu bên kia lưu là String
                "expert_profile_id_str": {"$toString": "$user_info.expert_profile_id"},
                # Giữ nguyên ID gốc để lookup nếu bên kia lưu là ObjectId
                "expert_profile_id_obj": "$user_info.expert_profile_id"
            }},

            # 3. Join bảng Expert Profiles
            # Chúng ta dùng $lookup pipeline phức tạp hơn để thử khớp cả 2 trường hợp (String hoặc ObjectId)
            {"$lookup": {
                "from": "expert_profiles",
                "let": {
                    "eid_str": "$expert_profile_id_str", 
                    "eid_obj": "$expert_profile_id_obj"
                },
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$or": [
                                # So sánh _id (của expert) với ID dạng String từ user
                                {"$eq": [{"$toString": "$_id"}, "$$eid_str"]},
                                # So sánh _id (của expert) với ID dạng ObjectId từ user
                                {"$eq": ["$_id", "$$eid_obj"]}
                            ]
                        }
                    }}
                ],
                "as": "expert_info"
            }},
            
            # 4. Unwind expert_info (giữ lại nếu null)
            {"$unwind": {
                "path": "$expert_info",
                "preserveNullAndEmptyArrays": True
            }},
            
            # 5. Project kết quả
            {"$project": {
                "_id": 0,
                "user_id": {"$toString": "$user_id"},
                "role": "$user_info.role",
                "liked_at": "$created_at",
                
                # Username: Ưu tiên lấy của Expert
                "username": {
                    "$cond": {
                        "if": {"$and": [
                            {"$eq": ["$user_info.role", "expert"]},
                            {"$ifNull": ["$expert_info", False]}
                        ]},
                        "then": "$expert_info.full_name",
                        "else": "$user_info.username"
                    }
                },
                
                # Avatar: Ưu tiên lấy của Expert
                "avatar_url": {
                    "$cond": {
                        "if": {"$and": [
                            {"$eq": ["$user_info.role", "expert"]},
                            {"$ifNull": ["$expert_info", False]}
                        ]},
                        "then": {"$ifNull": ["$expert_info.avatar_url", "$user_info.avatar_url"]},
                        "else": "$user_info.avatar_url"
                    }
                }
            }},
            {"$sort": {"liked_at": -1}}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(length=100)