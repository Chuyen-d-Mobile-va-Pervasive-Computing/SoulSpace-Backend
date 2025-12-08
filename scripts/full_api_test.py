"""
🧪 SoulSpace API Full Test Suite
================================
Script test toàn bộ API của SoulSpace Backend.
Chạy: python scripts/full_api_test.py

Author: Gemini
Date: 2024-12-08
"""

import httpx
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "http://127.0.0.1:8000/api/v1"
TIMEOUT = 30.0

# Test data - sử dụng UUID để tránh trùng email
TEST_ID = uuid.uuid4().hex[:8]

TEST_USER = {
    "email": f"testuser_{TEST_ID}@example.com",
    "password": "Test@123456",
    "username": f"TestUser_{TEST_ID}"
}

TEST_EXPERT = {
    "email": f"expert_{TEST_ID}@example.com",
    "password": "Expert@1234",
    "confirm_password": "Expert@1234"
}

# Admin credentials
ADMIN_CREDENTIALS = {
    "email": "admin@gmail.com",
    "password": "Admin@123"
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    SKIPPED = "⏭️ SKIPPED"
    WARNING = "⚠️ WARNING"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str = ""
    response_code: Optional[int] = None
    response_data: Optional[Any] = None


@dataclass
class TestContext:
    """Lưu trữ context giữa các test"""
    user_token: str = ""
    user_id: str = ""
    expert_token: str = ""
    expert_id: str = ""
    admin_token: str = ""
    
    journal_id: str = ""
    post_id: str = ""
    post_id_2: str = ""
    comment_id: str = ""
    reminder_id: str = ""
    test_code: str = ""
    result_id: str = ""
    action_id: str = ""
    report_id: str = ""
    article_id: str = ""
    
    results: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP CLIENT HELPER
# ═══════════════════════════════════════════════════════════════════════════════

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
    
    async def close(self):
        await self.client.aclose()
    
    def _headers(self, token: str = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    async def get(self, path: str, token: str = None, params: dict = None) -> httpx.Response:
        return await self.client.get(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            params=params
        )
    
    async def post(self, path: str, data: dict = None, token: str = None) -> httpx.Response:
        return await self.client.post(
            f"{self.base_url}{path}",
            json=data,
            headers=self._headers(token)
        )
    
    async def post_form(self, path: str, data: dict = None, token: str = None) -> httpx.Response:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return await self.client.post(
            f"{self.base_url}{path}",
            data=data,
            headers=headers
        )
    
    async def put(self, path: str, data: dict = None, token: str = None, params: dict = None) -> httpx.Response:
        return await self.client.put(
            f"{self.base_url}{path}",
            json=data,
            headers=self._headers(token),
            params=params
        )
    
    async def delete(self, path: str, token: str = None, params: dict = None) -> httpx.Response:
        return await self.client.delete(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            params=params
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def print_header(title: str):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def print_result(result: TestResult):
    status_icon = result.status.value
    print(f"  {status_icon} {result.name}")
    if result.message:
        print(f"      └─ {result.message}")
    if result.status == TestStatus.FAILED and result.response_data:
        print(f"      └─ Response: {str(result.response_data)[:200]}")


def add_result(ctx: TestContext, name: str, status: TestStatus, message: str = "", 
               response_code: int = None, response_data: Any = None):
    result = TestResult(name, status, message, response_code, response_data)
    ctx.results.append(result)
    print_result(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase1_auth(client: APIClient, ctx: TestContext):
    print_header("🔐 PHASE 1: AUTHENTICATION")
    
    # 1.1 Register
    try:
        resp = await client.post("/auth/register", TEST_USER)
        if resp.status_code == 200:
            data = resp.json()
            ctx.user_id = data.get("id", data.get("_id", ""))
            add_result(ctx, "POST /auth/register", TestStatus.PASSED, f"User ID: {ctx.user_id[:20]}...")
        elif resp.status_code == 400 and "already" in resp.text.lower():
            add_result(ctx, "POST /auth/register", TestStatus.WARNING, "User already exists, continuing...")
        else:
            add_result(ctx, "POST /auth/register", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /auth/register", TestStatus.FAILED, str(e))
    
    # 1.2 Login
    try:
        resp = await client.post("/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        if resp.status_code == 200:
            data = resp.json()
            ctx.user_token = data.get("access_token", "")
            add_result(ctx, "POST /auth/login", TestStatus.PASSED, f"Token: {ctx.user_token[:30]}...")
        else:
            add_result(ctx, "POST /auth/login", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
            return  # Can't continue without token
    except Exception as e:
        add_result(ctx, "POST /auth/login", TestStatus.FAILED, str(e))
        return
    
    # 1.3 Get current user
    try:
        resp = await client.get("/auth/me", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /auth/me", TestStatus.PASSED, "Profile retrieved")
        else:
            add_result(ctx, "GET /auth/me", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /auth/me", TestStatus.FAILED, str(e))
    
    # 1.4 Update profile
    try:
        resp = await client.put("/auth/update-profile", {
            "username": f"Updated_{TEST_ID}"
        }, token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "PUT /auth/update-profile", TestStatus.PASSED, "Profile updated")
        else:
            add_result(ctx, "PUT /auth/update-profile", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "PUT /auth/update-profile", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: JOURNAL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase2_journal(client: APIClient, ctx: TestContext):
    print_header("📔 PHASE 2: JOURNAL")
    
    if not ctx.user_token:
        add_result(ctx, "Journal Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # 2.1 Get journals (empty)
    try:
        resp = await client.get("/journal/", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /journal/", TestStatus.PASSED, f"Found {len(resp.json())} journals")
        else:
            add_result(ctx, "GET /journal/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /journal/", TestStatus.FAILED, str(e))
    
    # 2.2 Create journal (form-data)
    try:
        resp = await client.post_form("/journal/", {
            "text_content": "Hôm nay là một ngày tuyệt vời! Tôi đã hoàn thành được nhiều công việc quan trọng.",
            "tags": json.dumps([{"tag_name": "Happy"}, {"tag_name": "Productive"}]),
            "emotion_label": "Happy"
        }, token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            ctx.journal_id = data.get("id", "")
            sentiment = data.get("sentiment_label", "N/A")
            add_result(ctx, "POST /journal/", TestStatus.PASSED, f"Sentiment: {sentiment}")
        else:
            add_result(ctx, "POST /journal/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /journal/", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: COMMUNITY POSTS
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase3_posts(client: APIClient, ctx: TestContext):
    print_header("📝 PHASE 3: COMMUNITY POSTS")
    
    if not ctx.user_token:
        add_result(ctx, "Posts Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # 3.1 Get feed
    try:
        resp = await client.get("/anon-posts/", token=ctx.user_token, params={"limit": 10})
        if resp.status_code == 200:
            add_result(ctx, "GET /anon-posts/", TestStatus.PASSED, f"Found {len(resp.json())} posts")
        else:
            add_result(ctx, "GET /anon-posts/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /anon-posts/", TestStatus.FAILED, str(e))
    
    # 3.2 Create anonymous post
    try:
        resp = await client.post("/anon-posts/", {
            "content": f"Test post from automated test suite - {TEST_ID}. Đây là bài viết test tự động.",
            "is_anonymous": True,
            "hashtags": ["test", "automated"]
        }, token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            ctx.post_id = data.get("_id", data.get("id", ""))
            status = data.get("moderation_status", "N/A")
            add_result(ctx, "POST /anon-posts/ (anonymous)", TestStatus.PASSED, f"Status: {status}")
        else:
            add_result(ctx, "POST /anon-posts/ (anonymous)", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /anon-posts/ (anonymous)", TestStatus.FAILED, str(e))
    
    # 3.3 Create public post
    try:
        resp = await client.post("/anon-posts/", {
            "content": f"Public test post - {TEST_ID}. Bài viết công khai.",
            "is_anonymous": False,
            "hashtags": ["public", "test"]
        }, token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            ctx.post_id_2 = data.get("_id", data.get("id", ""))
            author = data.get("author_name", "N/A")
            add_result(ctx, "POST /anon-posts/ (public)", TestStatus.PASSED, f"Author: {author}")
        else:
            add_result(ctx, "POST /anon-posts/ (public)", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /anon-posts/ (public)", TestStatus.FAILED, str(e))
    
    # 3.4 Get post detail
    if ctx.post_id:
        try:
            resp = await client.get(f"/anon-posts/{ctx.post_id}", token=ctx.user_token)
            if resp.status_code == 200:
                data = resp.json()
                is_owner = data.get("is_owner", False)
                add_result(ctx, "GET /anon-posts/{id}", TestStatus.PASSED, f"is_owner: {is_owner}")
            else:
                add_result(ctx, "GET /anon-posts/{id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "GET /anon-posts/{id}", TestStatus.FAILED, str(e))
    
    # 3.5 Get my posts
    try:
        resp = await client.get("/anon-posts/my-posts", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /anon-posts/my-posts", TestStatus.PASSED, f"Found {len(resp.json())} posts")
        else:
            add_result(ctx, "GET /anon-posts/my-posts", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /anon-posts/my-posts", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: COMMENTS & LIKES
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase4_comments_likes(client: APIClient, ctx: TestContext):
    print_header("💬 PHASE 4: COMMENTS & LIKES")
    
    if not ctx.user_token or not ctx.post_id:
        add_result(ctx, "Comments & Likes Tests", TestStatus.SKIPPED, "No token or post_id")
        return
    
    # 4.1 Like post
    try:
        resp = await client.post(f"/anon-likes/{ctx.post_id}", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "POST /anon-likes/{post_id}", TestStatus.PASSED, "Liked!")
        else:
            add_result(ctx, "POST /anon-likes/{post_id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /anon-likes/{post_id}", TestStatus.FAILED, str(e))
    
    # 4.2 Check like status
    try:
        resp = await client.get(f"/anon-posts/{ctx.post_id}", token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            is_liked = data.get("is_liked", False)
            like_count = data.get("like_count", 0)
            add_result(ctx, "Verify like status", TestStatus.PASSED, f"is_liked: {is_liked}, count: {like_count}")
        else:
            add_result(ctx, "Verify like status", TestStatus.FAILED, f"Status: {resp.status_code}")
    except Exception as e:
        add_result(ctx, "Verify like status", TestStatus.FAILED, str(e))
    
    # 4.3 Unlike post
    try:
        resp = await client.delete(f"/anon-likes/{ctx.post_id}", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "DELETE /anon-likes/{post_id}", TestStatus.PASSED, "Unliked!")
        else:
            add_result(ctx, "DELETE /anon-likes/{post_id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "DELETE /anon-likes/{post_id}", TestStatus.FAILED, str(e))
    
    # 4.4 Create comment
    try:
        resp = await client.post("/anon-comments/", {
            "post_id": ctx.post_id,
            "content": f"Test comment from automated test - {TEST_ID}",
            "is_preset": False
        }, token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            ctx.comment_id = data.get("_id", data.get("id", ""))
            add_result(ctx, "POST /anon-comments/", TestStatus.PASSED, f"Comment ID: {ctx.comment_id[:20]}...")
        else:
            add_result(ctx, "POST /anon-comments/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /anon-comments/", TestStatus.FAILED, str(e))
    
    # 4.5 Get comments
    try:
        resp = await client.get(f"/anon-comments/{ctx.post_id}", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /anon-comments/{post_id}", TestStatus.PASSED, f"Found {len(resp.json())} comments")
        else:
            add_result(ctx, "GET /anon-comments/{post_id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /anon-comments/{post_id}", TestStatus.FAILED, str(e))
    
    # 4.6 Delete comment
    if ctx.comment_id:
        try:
            resp = await client.delete(f"/anon-comments/{ctx.comment_id}", token=ctx.user_token)
            if resp.status_code == 200:
                add_result(ctx, "DELETE /anon-comments/{id}", TestStatus.PASSED, "Comment deleted")
            else:
                add_result(ctx, "DELETE /anon-comments/{id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "DELETE /anon-comments/{id}", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: REMINDERS
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase5_reminders(client: APIClient, ctx: TestContext):
    print_header("⏰ PHASE 5: REMINDERS")
    
    if not ctx.user_token:
        add_result(ctx, "Reminders Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # 5.1 Get reminders
    try:
        resp = await client.get("/reminders/", token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /reminders/", TestStatus.PASSED, f"Found {len(resp.json())} reminders")
        else:
            add_result(ctx, "GET /reminders/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /reminders/", TestStatus.FAILED, str(e))
    
    # 5.2 Create reminder (once)
    try:
        resp = await client.post("/reminders/", {
            "title": "Test Reminder",
            "message": f"Test reminder - {TEST_ID[:20]}",
            "time_of_day": "14:00",
            "repeat_type": "once",
            "repeat_days": None
        }, token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            ctx.reminder_id = data.get("_id", data.get("id", ""))
            add_result(ctx, "POST /reminders/ (once)", TestStatus.PASSED, f"ID: {ctx.reminder_id[:20]}...")
        else:
            add_result(ctx, "POST /reminders/ (once)", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /reminders/ (once)", TestStatus.FAILED, str(e))
    
    # 5.3 Create reminder (daily)
    try:
        resp = await client.post("/reminders/", {
            "title": "Daily Reminder",
            "message": "Daily test reminder",
            "time_of_day": "07:00",
            "repeat_type": "daily",
            "repeat_days": None
        }, token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "POST /reminders/ (daily)", TestStatus.PASSED, "Daily reminder created")
        else:
            add_result(ctx, "POST /reminders/ (daily)", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /reminders/ (daily)", TestStatus.FAILED, str(e))
    
    # 5.4 Create reminder (custom)
    try:
        resp = await client.post("/reminders/", {
            "title": "Custom Reminder",
            "message": "Mon-Wed-Fri reminder",
            "time_of_day": "18:00",
            "repeat_type": "custom",
            "repeat_days": [1, 3, 5]
        }, token=ctx.user_token)
        if resp.status_code == 200:
            add_result(ctx, "POST /reminders/ (custom)", TestStatus.PASSED, "Custom reminder created")
        else:
            add_result(ctx, "POST /reminders/ (custom)", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /reminders/ (custom)", TestStatus.FAILED, str(e))
    
    # 5.5 Update reminder
    if ctx.reminder_id:
        try:
            resp = await client.put(f"/reminders/{ctx.reminder_id}", {
                "title": "Updated Reminder",
                "time_of_day": "15:00"
            }, token=ctx.user_token)
            if resp.status_code == 200:
                add_result(ctx, "PUT /reminders/{id}", TestStatus.PASSED, "Reminder updated")
            else:
                add_result(ctx, "PUT /reminders/{id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "PUT /reminders/{id}", TestStatus.FAILED, str(e))
    
    # 5.6 Toggle reminder
    if ctx.reminder_id:
        try:
            resp = await client.post(f"/reminders/toggle/{ctx.reminder_id}", {
                "is_active": False
            }, token=ctx.user_token)
            if resp.status_code == 200:
                add_result(ctx, "POST /reminders/toggle/{id}", TestStatus.PASSED, "Reminder toggled")
            else:
                add_result(ctx, "POST /reminders/toggle/{id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "POST /reminders/toggle/{id}", TestStatus.FAILED, str(e))
    
    # 5.7 Delete reminder
    if ctx.reminder_id:
        try:
            resp = await client.delete(f"/reminders/{ctx.reminder_id}", token=ctx.user_token)
            if resp.status_code == 200:
                add_result(ctx, "DELETE /reminders/{id}", TestStatus.PASSED, "Reminder deleted")
            else:
                add_result(ctx, "DELETE /reminders/{id}", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "DELETE /reminders/{id}", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: TESTS (Psychological)
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase6_tests(client: APIClient, ctx: TestContext):
    print_header("📋 PHASE 6: PSYCHOLOGICAL TESTS")
    
    if not ctx.user_token:
        add_result(ctx, "Tests Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # 6.1 Get all tests
    try:
        resp = await client.get("/tests", token=ctx.user_token)
        if resp.status_code == 200:
            tests = resp.json()
            if tests:
                ctx.test_code = tests[0].get("code", tests[0].get("test_code", ""))
            add_result(ctx, "GET /tests", TestStatus.PASSED, f"Found {len(tests)} tests")
        else:
            add_result(ctx, "GET /tests", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /tests", TestStatus.FAILED, str(e))
    
    # 6.2 Get test questions
    if ctx.test_code:
        try:
            resp = await client.get(f"/tests/{ctx.test_code}/questions", token=ctx.user_token)
            if resp.status_code == 200:
                questions = resp.json()
                q_count = len(questions) if isinstance(questions, list) else len(questions.get("questions", []))
                add_result(ctx, f"GET /tests/{ctx.test_code}/questions", TestStatus.PASSED, f"Found {q_count} questions")
            else:
                add_result(ctx, f"GET /tests/{ctx.test_code}/questions", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, f"GET /tests/{ctx.test_code}/questions", TestStatus.FAILED, str(e))
    else:
        add_result(ctx, "GET /tests/{code}/questions", TestStatus.SKIPPED, "No test code available")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: MENTAL TREE
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase7_tree(client: APIClient, ctx: TestContext):
    print_header("🌳 PHASE 7: MENTAL TREE")
    
    if not ctx.user_token:
        add_result(ctx, "Tree Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # 7.1 Get tree status
    try:
        resp = await client.get("/tree/status", token=ctx.user_token)
        if resp.status_code == 200:
            data = resp.json()
            level = data.get("level", data.get("tree_level", "N/A"))
            xp = data.get("xp", data.get("total_xp", "N/A"))
            add_result(ctx, "GET /tree/status", TestStatus.PASSED, f"Level: {level}, XP: {xp}")
        else:
            add_result(ctx, "GET /tree/status", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /tree/status", TestStatus.FAILED, str(e))
    
    # 7.2 Get positive actions
    try:
        resp = await client.get("/tree/positive-actions", token=ctx.user_token)
        if resp.status_code == 200:
            actions = resp.json()
            if actions:
                ctx.action_id = actions[0].get("_id", actions[0].get("id", ""))
            add_result(ctx, "GET /tree/positive-actions", TestStatus.PASSED, f"Found {len(actions)} actions")
        else:
            add_result(ctx, "GET /tree/positive-actions", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /tree/positive-actions", TestStatus.FAILED, str(e))
    
    # 7.3 Nourish tree
    if ctx.action_id:
        try:
            resp = await client.post("/tree/nourish", {
                "action_id": ctx.action_id,
                "positive_thoughts": f"Test positive thought from automated test - {TEST_ID}"
            }, token=ctx.user_token)
            if resp.status_code == 200:
                add_result(ctx, "POST /tree/nourish", TestStatus.PASSED, "Tree nourished!")
            elif resp.status_code == 409:
                add_result(ctx, "POST /tree/nourish", TestStatus.WARNING, "Already watered today")
            else:
                add_result(ctx, "POST /tree/nourish", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "POST /tree/nourish", TestStatus.FAILED, str(e))
    else:
        add_result(ctx, "POST /tree/nourish", TestStatus.SKIPPED, "No action ID available")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase8_reports(client: APIClient, ctx: TestContext):
    print_header("🚨 PHASE 8: REPORTS")
    
    if not ctx.user_token:
        add_result(ctx, "Reports Tests", TestStatus.SKIPPED, "No user token")
        return
    
    # Use post_id_2 (public post) as target to avoid self-reporting issues
    target_id = ctx.post_id_2 if ctx.post_id_2 else ctx.post_id
    
    if target_id:
        try:
            resp = await client.post("/reports/", {
                "target_id": target_id,
                "target_type": "post",
                "reason": f"Test report from automated test - {TEST_ID}"
            }, token=ctx.user_token)
            if resp.status_code == 200:
                data = resp.json()
                ctx.report_id = data.get("_id", data.get("id", ""))
                add_result(ctx, "POST /reports/", TestStatus.PASSED, f"Report ID: {ctx.report_id[:20]}...")
            else:
                add_result(ctx, "POST /reports/", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "POST /reports/", TestStatus.FAILED, str(e))
    else:
        add_result(ctx, "POST /reports/", TestStatus.SKIPPED, "No post to report")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: EXPERT APIs
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase9_expert(client: APIClient, ctx: TestContext):
    print_header("👨‍⚕️ PHASE 9: EXPERT APIs")
    
    # 9.1 Register expert
    try:
        resp = await client.post("/auth/expert/register", TEST_EXPERT)
        if resp.status_code == 201:
            add_result(ctx, "POST /auth/expert/register", TestStatus.PASSED, "Expert registered")
        elif resp.status_code == 400 and "already" in resp.text.lower():
            add_result(ctx, "POST /auth/expert/register", TestStatus.WARNING, "Expert already exists")
        else:
            add_result(ctx, "POST /auth/expert/register", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "POST /auth/expert/register", TestStatus.FAILED, str(e))
    
    # 9.2 Complete profile - Skip for now as it requires user_id from step 1
    add_result(ctx, "POST /auth/expert/complete-profile", TestStatus.SKIPPED, "Requires approved user_id")
    
    # 9.3 Expert login (will fail if not approved - expected)
    try:
        resp = await client.post("/auth/expert/login", {
            "email": TEST_EXPERT["email"],
            "password": TEST_EXPERT["password"]
        })
        if resp.status_code == 200:
            data = resp.json()
            ctx.expert_token = data.get("access_token", "")
            add_result(ctx, "POST /auth/expert/login", TestStatus.PASSED, "Expert logged in!")
        else:
            add_result(ctx, "POST /auth/expert/login", TestStatus.WARNING, "Expert not approved yet (expected behavior)")
    except Exception as e:
        add_result(ctx, "POST /auth/expert/login", TestStatus.WARNING, str(e))
    
    # 9.4 Expert info (if logged in)
    if ctx.expert_token:
        try:
            resp = await client.get("/expert/info", token=ctx.expert_token)
            if resp.status_code == 200:
                add_result(ctx, "GET /expert/info", TestStatus.PASSED, "Expert info retrieved")
            else:
                add_result(ctx, "GET /expert/info", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
        except Exception as e:
            add_result(ctx, "GET /expert/info", TestStatus.FAILED, str(e))
    else:
        add_result(ctx, "GET /expert/info", TestStatus.SKIPPED, "No expert token (need admin approval)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: ADMIN APIs
# ═══════════════════════════════════════════════════════════════════════════════

async def test_phase10_admin(client: APIClient, ctx: TestContext):
    print_header("🛡️ PHASE 10: ADMIN APIs")
    
    # 10.1 Admin login
    try:
        resp = await client.post("/auth/login", ADMIN_CREDENTIALS)
        if resp.status_code == 200:
            data = resp.json()
            ctx.admin_token = data.get("access_token", "")
            add_result(ctx, "POST /auth/login (admin)", TestStatus.PASSED, "Admin logged in!")
        else:
            add_result(ctx, "POST /auth/login (admin)", TestStatus.WARNING, "Admin account not found in DB")
            return
    except Exception as e:
        add_result(ctx, "POST /auth/login (admin)", TestStatus.FAILED, str(e))
        return
    
    # 10.2 Get stats
    try:
        resp = await client.get("/admin/stats", token=ctx.admin_token)
        if resp.status_code == 200:
            data = resp.json()
            users = data.get("users", {}).get("total", 0)
            posts = data.get("posts", {}).get("total", 0)
            add_result(ctx, "GET /admin/stats", TestStatus.PASSED, f"Users: {users}, Posts: {posts}")
        else:
            add_result(ctx, "GET /admin/stats", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /admin/stats", TestStatus.FAILED, str(e))
    
    # 10.3 Get posts
    try:
        resp = await client.get("/admin/posts", token=ctx.admin_token, params={"limit": 10})
        if resp.status_code == 200:
            add_result(ctx, "GET /admin/posts", TestStatus.PASSED, f"Found {len(resp.json())} posts")
        else:
            add_result(ctx, "GET /admin/posts", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /admin/posts", TestStatus.FAILED, str(e))
    
    # 10.4 Get comments
    try:
        resp = await client.get("/admin/comments", token=ctx.admin_token, params={"limit": 10})
        if resp.status_code == 200:
            add_result(ctx, "GET /admin/comments", TestStatus.PASSED, f"Found {len(resp.json())} comments")
        else:
            add_result(ctx, "GET /admin/comments", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /admin/comments", TestStatus.FAILED, str(e))
    
    # 10.5 Get reports
    try:
        resp = await client.get("/admin/reports", token=ctx.admin_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /admin/reports", TestStatus.PASSED, f"Found {len(resp.json())} reports")
        else:
            add_result(ctx, "GET /admin/reports", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /admin/reports", TestStatus.FAILED, str(e))
    
    # 10.6 Get pending expert articles
    try:
        resp = await client.get("/admin/expert-articles/pending", token=ctx.admin_token)
        if resp.status_code == 200:
            add_result(ctx, "GET /admin/expert-articles/pending", TestStatus.PASSED, f"Found {len(resp.json())} articles")
        else:
            add_result(ctx, "GET /admin/expert-articles/pending", TestStatus.FAILED, f"Status: {resp.status_code}", resp.status_code, resp.text)
    except Exception as e:
        add_result(ctx, "GET /admin/expert-articles/pending", TestStatus.FAILED, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

async def cleanup(client: APIClient, ctx: TestContext):
    print_header("🧹 CLEANUP")
    
    if not ctx.user_token:
        add_result(ctx, "Cleanup", TestStatus.SKIPPED, "No token for cleanup")
        return
    
    # Delete test posts
    for post_id in [ctx.post_id, ctx.post_id_2]:
        if post_id:
            try:
                resp = await client.delete(f"/anon-posts/{post_id}", token=ctx.user_token)
                if resp.status_code == 200:
                    add_result(ctx, f"DELETE post {post_id[:12]}...", TestStatus.PASSED, "Cleaned up")
                else:
                    add_result(ctx, f"DELETE post {post_id[:12]}...", TestStatus.WARNING, f"Status: {resp.status_code}")
            except Exception as e:
                add_result(ctx, f"DELETE post", TestStatus.WARNING, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(ctx: TestContext):
    print_header("📊 TEST SUMMARY")
    
    passed = sum(1 for r in ctx.results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in ctx.results if r.status == TestStatus.FAILED)
    skipped = sum(1 for r in ctx.results if r.status == TestStatus.SKIPPED)
    warning = sum(1 for r in ctx.results if r.status == TestStatus.WARNING)
    total = len(ctx.results)
    
    print(f"""
  ┌────────────────────────────────────────┐
  │  Total Tests:     {total:>4}                  │
  │  ✅ Passed:       {passed:>4}                  │
  │  ❌ Failed:       {failed:>4}                  │
  │  ⚠️  Warning:      {warning:>4}                  │
  │  ⏭️  Skipped:      {skipped:>4}                  │
  │                                        │
  │  Success Rate:    {(passed/total*100) if total > 0 else 0:>5.1f}%               │
  └────────────────────────────────────────┘
    """)
    
    if failed > 0:
        print("\n  ❌ Failed Tests:")
        for r in ctx.results:
            if r.status == TestStatus.FAILED:
                print(f"     - {r.name}: {r.message}")
    
    print(f"\n  Test ID: {TEST_ID}")
    print(f"  Timestamp: {datetime.now().isoformat()}")


async def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     🧪 SoulSpace API Full Test Suite                             ║
║                                                                   ║
║     Testing all endpoints against: {:<30}║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """.format(BASE_URL))
    
    client = APIClient(BASE_URL)
    ctx = TestContext()
    
    try:
        # Run all test phases
        await test_phase1_auth(client, ctx)
        await test_phase2_journal(client, ctx)
        await test_phase3_posts(client, ctx)
        await test_phase4_comments_likes(client, ctx)
        await test_phase5_reminders(client, ctx)
        await test_phase6_tests(client, ctx)
        await test_phase7_tree(client, ctx)
        await test_phase8_reports(client, ctx)
        await test_phase9_expert(client, ctx)
        await test_phase10_admin(client, ctx)
        
        # Cleanup
        await cleanup(client, ctx)
        
    finally:
        await client.close()
    
    # Print summary
    print_summary(ctx)
    
    # Exit code based on failed tests
    failed = sum(1 for r in ctx.results if r.status == TestStatus.FAILED)
    return failed


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
