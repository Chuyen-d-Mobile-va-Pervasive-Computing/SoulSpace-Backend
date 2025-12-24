from typing import List, Optional
from app.repositories.anon_post_repository import AnonPostRepository
from app.repositories.expert_article_repository import ExpertArticleRepository
from app.schemas.common.feed_schema import FeedItemResponse

class FeedService:
    def __init__(self, db):
        self.anon_post_repo = AnonPostRepository(db)
        self.expert_article_repo = ExpertArticleRepository(db)

    async def get_mixed_feed(self, limit: int = 20, current_user_id: Optional[str] = None) -> List[FeedItemResponse]:
        """
        Lấy Newsfeed tổng hợp từ User Posts và Expert Articles.
        Sắp xếp theo thời gian tạo mới nhất.
        """
        
        # 1. Lấy User Posts (đã approved)
        # Lấy dư ra một chút (limit) để khi merge vẫn đủ dữ liệu mới nhất
        user_posts = await self.anon_post_repo.list(limit=limit, current_user_id=current_user_id)
        
        # 2. Lấy Expert Articles (đã approved)
        expert_articles = await self.expert_article_repo.list_approved_feed(limit=limit, current_user_id=current_user_id)
        
        # 3. Chuẩn hóa dữ liệu về FeedItemResponse trước khi merge
        feed_items = []

        # Convert User Posts
        for post in user_posts:
            # Xác định avatar và author name cho user
            # Logic anon_post_repo._enrich_post đã xử lý tên, ở đây ta map sang schema chung
            
            # Nếu là post thường thì không có title
            feed_items.append({
                "_id": post["_id"],
                "type": "user_post",
                "author_id": post.get("user_id") or "anonymous",
                "author_name": post.get("author_name", "Ẩn danh"),
                "author_avatar": None, # Hiện tại user post chưa trả về avatar trong repo, có thể bổ sung sau
                "author_role": "user",
                "content": post.get("content", ""),
                "title": None,
                "image_url": post.get("image_url"),
                "hashtags": post.get("hashtags", []),
                "like_count": post.get("like_count", 0),
                "comment_count": post.get("comment_count", 0),
                "is_liked": post.get("is_liked", False),
                "is_owner": post.get("is_owner", False),
                "created_at": post.get("created_at")
            })

        # Convert Expert Articles
        for article in expert_articles:
            # Sử dụng approved_at làm mốc thời gian hiển thị cho bài PR (hoặc created_at tùy logic)
            # Thường bài PR tính lúc approved mới public
            display_time = article.get("approved_at") or article.get("created_at")
            
            feed_items.append({
                "_id": article["_id"],
                "type": "expert_article",
                "author_id": article.get("author_id"),
                "author_name": article.get("author_name"),
                "author_avatar": article.get("author_avatar"),
                "author_role": "expert",
                "content": article.get("content", ""),
                "title": article.get("title"),
                "image_url": article.get("image_url"),
                "hashtags": article.get("hashtags", []),
                "like_count": article.get("like_count", 0),
                "comment_count": article.get("comment_count", 0),
                "is_liked": article.get("is_liked", False),
                "is_owner": article.get("is_owner", False),
                "created_at": display_time
            })

        # 4. Gộp và Sắp xếp (Newest first)
        # Sort key là created_at
        feed_items.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 5. Cắt đúng limit
        final_feed = feed_items[:limit]
        
        # 6. Map sang Pydantic Model để validate lần cuối
        return [FeedItemResponse(**item) for item in final_feed]