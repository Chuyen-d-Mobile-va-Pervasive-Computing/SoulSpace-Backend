import asyncio
import os
import sys
import certifi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def create_indexes():
    client = AsyncIOMotorClient(settings.MONGO_URI, tlsCAFile=certifi.where())
    db = client[settings.DATABASE_NAME]

    # Users
    await db.users.create_index([("email", 1)], unique=True)
    await db.users.create_index([("username", 1)])

    # Tests
    await db.tests.create_index([("test_code", 1)], unique=True)
    await db.tests.create_index([("_id", 1)])

    # Test_Questions
    await db.test_questions.create_index([("test_id", 1)])

    # User_Test_Results
    await db.user_test_results.create_index([("user_id", 1), ("test_id", 1), ("completed_at", 1)])

    # Journals
    await db.journals.create_index([("user_id", 1), ("created_at", 1)])
    await db.journals.create_index([("tags.tag_name", 1)])

    # Positive_Actions
    await db.positive_actions.create_index([("_id", 1)])

    # User_Tree
    await db.user_tree.create_index([("user_id", 1)], unique=True)
    await db.user_tree.create_index([("last_watered_at", 1)])

    # Anon_Posts
    await db.anon_posts.create_index([("user_id", 1), ("created_at", 1), ("moderation_status", 1)])

    # Anon_Comments
    await db.anon_comments.create_index([("post_id", 1), ("created_at", 1)])

    # Anon_Likes
    await db.anon_likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)

    # Sensitive_Keywords
    await db.sensitive_keywords.create_index([("keyword", 1), ("language", 1)])

    # Moderation_Logs
    await db.moderation_logs.create_index([("entity_type", 1), ("entity_id", 1), ("timestamp", 1)])

    # Reminders
    await db.reminders.create_index([("user_id", 1), ("remind_time", 1)])

    # Challenges
    await db.challenges.create_index([("_id", 1)])

    # User_Challenges
    await db.user_challenges.create_index([("user_id", 1), ("challenge_id", 1)])

    # Badges
    await db.badges.create_index([("_id", 1), ("challenge_id", 1)])

    # User_Badges
    await db.user_badges.create_index([("user_id", 1), ("badge_id", 1)])

    print("Indexes created successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())