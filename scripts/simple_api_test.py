"""
Simple API Test - No fancy output
"""
import httpx
import asyncio
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_ID = uuid.uuid4().hex[:8]

TEST_USER = {
    "email": f"testuser_{TEST_ID}@example.com",
    "password": "Test@123456",
    "username": f"TestUser_{TEST_ID}"
}

ADMIN_CREDENTIALS = {
    "email": "admin@gmail.com",
    "password": "Admin@123"
}

results = {"passed": [], "failed": [], "skipped": []}

async def test(name, method, path, token=None, data=None, expected_codes=[200]):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if method == "GET":
                resp = await client.get(f"{BASE_URL}{path}", headers=headers)
            elif method == "POST":
                resp = await client.post(f"{BASE_URL}{path}", json=data, headers=headers)
            elif method == "POST_FORM":
                del headers["Content-Type"]
                resp = await client.post(f"{BASE_URL}{path}", data=data, headers=headers)
            elif method == "PUT":
                resp = await client.put(f"{BASE_URL}{path}", json=data, headers=headers)
            elif method == "DELETE":
                resp = await client.delete(f"{BASE_URL}{path}", headers=headers)
            
            if resp.status_code in expected_codes:
                results["passed"].append(name)
                print(f"[PASS] {name}")
                return resp.json() if resp.text else {}
            else:
                results["failed"].append(f"{name} - Status: {resp.status_code}")
                print(f"[FAIL] {name} - Status: {resp.status_code}")
                return None
        except Exception as e:
            results["failed"].append(f"{name} - Error: {str(e)[:50]}")
            print(f"[FAIL] {name} - {str(e)[:50]}")
            return None

async def main():
    print(f"\n=== API TEST START (ID: {TEST_ID}) ===\n")
    
    # Phase 1: Auth
    print("--- PHASE 1: AUTH ---")
    await test("Register", "POST", "/auth/register", data=TEST_USER, expected_codes=[200, 400])
    
    login_resp = await test("Login", "POST", "/auth/login", data={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    token = login_resp.get("access_token", "") if login_resp else ""
    
    if not token:
        print("[SKIP] No token, cannot continue")
        return
    
    await test("Get Me", "GET", "/auth/me", token=token)
    
    # Phase 2: Journal
    print("\n--- PHASE 2: JOURNAL ---")
    await test("Get Journals", "GET", "/journal/", token=token)
    journal = await test("Create Journal", "POST_FORM", "/journal/", token=token, data={
        "text_content": "Test journal entry",
        "emotion_label": "Happy"
    })
    
    # Phase 3: Posts
    print("\n--- PHASE 3: POSTS ---")
    await test("Get Posts", "GET", "/anon-posts/", token=token)
    
    # Use clean content that won't trigger moderation
    post = await test("Create Post", "POST", "/anon-posts/", token=token, data={
        "content": f"This is a wonderful day to learn something new. ID {TEST_ID}",
        "is_anonymous": True,
        "hashtags": ["happy", "learning"]
    })
    post_id = post.get("_id", "") if post else ""
    post_status = post.get("moderation_status", "") if post else ""
    print(f"    Post ID: {post_id[:20]}..., Status: {post_status}")
    
    await test("Get My Posts", "GET", "/anon-posts/my-posts", token=token)
    
    # Phase 4: Likes & Comments
    print("\n--- PHASE 4: LIKES & COMMENTS ---")
    if post_id:
        await test("Like Post", "POST", f"/anon-likes/{post_id}", token=token)
        await test("Unlike Post", "DELETE", f"/anon-likes/{post_id}", token=token)
        
        # Use clean content for comment
        comment = await test("Create Comment", "POST", "/anon-comments/", token=token, data={
            "post_id": post_id,
            "content": "What a great and positive message!",
            "is_preset": False
        })
        comment_id = comment.get("_id", "") if comment else ""
        comment_status = comment.get("moderation_status", "") if comment else ""
        print(f"    Comment ID: {comment_id[:20] if comment_id else 'None'}..., Status: {comment_status}")
        
        await test("Get Comments", "GET", f"/anon-comments/{post_id}", token=token)
        
        # Only try to delete if we got a comment_id
        if comment_id:
            await test("Delete Comment", "DELETE", f"/anon-comments/{comment_id}", token=token)
        else:
            print("[SKIP] Delete Comment - No comment_id")
    
    # Cleanup should happen at the end after all tests
    cleanup_post_id = post_id  # Save for later
    
    # Phase 5: Reminders
    print("\n--- PHASE 5: REMINDERS ---")
    await test("Get Reminders", "GET", "/reminders/", token=token)
    reminder = await test("Create Reminder", "POST", "/reminders/", token=token, data={
        "title": "Test",
        "message": "Test reminder",
        "time_of_day": "14:00",
        "repeat_type": "once"
    })
    reminder_id = reminder.get("_id", "") if reminder else ""
    
    if reminder_id:
        await test("Delete Reminder", "DELETE", f"/reminders/{reminder_id}", token=token)
    
    # Phase 6: Tests
    print("\n--- PHASE 6: TESTS ---")
    tests = await test("Get Tests", "GET", "/tests", token=token)
    
    # Phase 7: Tree
    print("\n--- PHASE 7: TREE ---")
    await test("Get Tree Status", "GET", "/tree/status", token=token)
    actions = await test("Get Positive Actions", "GET", "/tree/positive-actions", token=token)
    
    # Phase 8: Reports
    print("\n--- PHASE 8: REPORTS ---")
    if post_id:
        await test("Create Report", "POST", "/reports/", token=token, data={
            "target_id": post_id,
            "target_type": "post",
            "reason": "Test report"
        })
    
    # Phase 9: Admin
    print("\n--- PHASE 9: ADMIN ---")
    admin_login = await test("Admin Login", "POST", "/auth/login", data=ADMIN_CREDENTIALS)
    admin_token = admin_login.get("access_token", "") if admin_login else ""
    
    if admin_token:
        await test("Admin Stats", "GET", "/admin/stats", token=admin_token)
        await test("Admin Posts", "GET", "/admin/posts?limit=5", token=admin_token)
        await test("Admin Comments", "GET", "/admin/comments?limit=5", token=admin_token)
        await test("Admin Reports", "GET", "/admin/reports", token=admin_token)
        await test("Admin Users", "GET", "/admin/users?limit=5", token=admin_token)
    else:
        print("[SKIP] No admin token")
    
    # Cleanup
    print("\n--- CLEANUP ---")
    if cleanup_post_id:
        await test("Delete Post", "DELETE", f"/anon-posts/{cleanup_post_id}", token=token)
    else:
        print("[SKIP] Delete Post - No post_id")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"PASSED: {len(results['passed'])}")
    print(f"FAILED: {len(results['failed'])}")
    
    if results["failed"]:
        print(f"\nFailed tests:")
        for f in results["failed"]:
            print(f"  - {f}")
    
    print(f"\nTest ID: {TEST_ID}")

if __name__ == "__main__":
    asyncio.run(main())
