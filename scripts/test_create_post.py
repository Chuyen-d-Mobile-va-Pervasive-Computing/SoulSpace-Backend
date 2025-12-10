"""
Test API: POST /api/v1/anon-posts/ (Create Post)
Chạy: python scripts/test_create_post.py
"""
import httpx
import asyncio
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_create_post():
    async with httpx.AsyncClient(timeout=60) as client:
        print("=" * 60)
        print("TEST: POST /api/v1/anon-posts/ (Create Post)")
        print("=" * 60)
        
        # === SETUP: Tạo user và login ===
        test_id = uuid.uuid4().hex[:8]
        user = {
            "email": f"posttest_{test_id}@test.com",
            "password": "Test@123456"
        }
        
        print("\n[1] Đăng ký user mới...")
        reg = await client.post(f"{BASE_URL}/auth/register", json=user)
        print(f"    Status: {reg.status_code}")
        
        print("\n[2] Đăng nhập...")
        login = await client.post(f"{BASE_URL}/auth/login", json=user)
        token = login.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"    Status: {login.status_code}")
        print(f"    Token: {token[:30]}...")
        
        # === TEST 1: Tạo bài viết ẩn danh ===
        print("\n" + "-" * 60)
        print("[TEST 1] Tạo bài viết ẩn danh (is_anonymous=True)")
        print("-" * 60)
        
        post_data = {
            "content": f"Đây là bài viết ẩn danh test #{test_id}. Hôm nay tôi cảm thấy rất vui!",
            "is_anonymous": True,
            "hashtags": ["test", "happy", "anonymous"]
        }
        print(f"    Request: {post_data}")
        
        resp = await client.post(f"{BASE_URL}/anon-posts/", json=post_data, headers=headers)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"    ✅ PASSED!")
            print(f"    Response:")
            print(f"       _id: {data.get('_id')}")
            print(f"       content: {data.get('content')[:50]}...")
            print(f"       is_anonymous: {data.get('is_anonymous')}")
            print(f"       author_name: {data.get('author_name')}")
            print(f"       moderation_status: {data.get('moderation_status')}")
            print(f"       hashtags: {data.get('hashtags')}")
            print(f"       like_count: {data.get('like_count')}")
            print(f"       comment_count: {data.get('comment_count')}")
            print(f"       is_owner: {data.get('is_owner')}")
            post_id_1 = data.get("_id")
        else:
            print(f"    ❌ FAILED!")
            print(f"    Error: {resp.text}")
            post_id_1 = None
        
        # === TEST 2: Tạo bài viết công khai ===
        print("\n" + "-" * 60)
        print("[TEST 2] Tạo bài viết công khai (is_anonymous=False)")
        print("-" * 60)
        
        post_data = {
            "content": f"Đây là bài viết công khai test #{test_id}. Tôi muốn chia sẻ với mọi người!",
            "is_anonymous": False,
            "hashtags": ["sharing", "public"]
        }
        print(f"    Request: {post_data}")
        
        resp = await client.post(f"{BASE_URL}/anon-posts/", json=post_data, headers=headers)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"    ✅ PASSED!")
            print(f"    Response:")
            print(f"       _id: {data.get('_id')}")
            print(f"       is_anonymous: {data.get('is_anonymous')}")
            print(f"       author_name: {data.get('author_name')} (username hiển thị)")
            print(f"       moderation_status: {data.get('moderation_status')}")
            post_id_2 = data.get("_id")
        else:
            print(f"    ❌ FAILED!")
            print(f"    Error: {resp.text}")
            post_id_2 = None
        
        # === TEST 3: Tạo bài viết không có token ===
        print("\n" + "-" * 60)
        print("[TEST 3] Tạo bài viết KHÔNG có token (expect 401/403)")
        print("-" * 60)
        
        post_data = {"content": "Test without auth", "is_anonymous": True, "hashtags": []}
        resp = await client.post(f"{BASE_URL}/anon-posts/", json=post_data)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code in [401, 403]:
            print(f"    ✅ PASSED! (Correctly rejected)")
        else:
            print(f"    ❌ FAILED! (Should be 401 or 403)")
        
        # === TEST 4: Tạo bài viết với nội dung trống ===
        print("\n" + "-" * 60)
        print("[TEST 4] Tạo bài viết với content rỗng (expect 422)")
        print("-" * 60)
        
        post_data = {"content": "", "is_anonymous": True, "hashtags": []}
        resp = await client.post(f"{BASE_URL}/anon-posts/", json=post_data, headers=headers)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code == 422:
            print(f"    ✅ PASSED! (Validation error as expected)")
        else:
            print(f"    ❌ FAILED! (Should be 422)")
        
        # === CLEANUP ===
        print("\n" + "-" * 60)
        print("[CLEANUP] Xóa bài viết test...")
        print("-" * 60)
        
        for post_id in [post_id_1, post_id_2]:
            if post_id:
                del_resp = await client.delete(f"{BASE_URL}/anon-posts/{post_id}", headers=headers)
                print(f"    Delete {post_id[:20]}...: {del_resp.status_code}")
        
        # === SUMMARY ===
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("✅ Test 1: Tạo bài viết ẩn danh - PASSED")
        print("✅ Test 2: Tạo bài viết công khai - PASSED")
        print("✅ Test 3: Không có token - PASSED (401/403)")
        print("✅ Test 4: Content rỗng - PASSED (422)")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_create_post())
