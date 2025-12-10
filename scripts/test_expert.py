import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        print("=== TEST EXPERT LOGIN ===")
        
        # Login expert
        expert = {"email": "expert@gmail.com", "password": "Expert@123"}
        print(f"Credentials: {expert}")
        
        login = await client.post("http://127.0.0.1:8000/api/v1/auth/login", json=expert)
        print(f"Status: {login.status_code}")
        print(f"Response: {login.json()}")
        
        if login.status_code == 200:
            data = login.json()
            print(f"\n=== LOGIN SUCCESS ===")
            print(f"Role: {data.get('role')}")
            print(f"Username: {data.get('username')}")
            token = data.get("access_token", "")
            print(f"Token: {token[:50]}...")
            
            # Test access to user APIs
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n=== TEST API ACCESS ===")
            
            # Test get me
            me = await client.get("http://127.0.0.1:8000/api/v1/auth/me", headers=headers)
            print(f"GET /auth/me: {me.status_code}")
            
            # Test get my profile (NEW)
            my_profile = await client.get("http://127.0.0.1:8000/api/v1/expert/my-profile", headers=headers)
            print(f"GET /expert/my-profile: {my_profile.status_code}")
            if my_profile.status_code == 200:
                profile_data = my_profile.json()
                print(f"   profile_id: {profile_data.get('profile_id')}")
                print(f"   full_name: {profile_data.get('full_name')}")
                print(f"   status: {profile_data.get('status')}")
            else:
                print(f"   Response: {my_profile.text[:200]}")
            
            # Test create post
            post_resp = await client.post("http://127.0.0.1:8000/api/v1/anon-posts/", json={
                "content": "Expert test post",
                "is_anonymous": True,
                "hashtags": []
            }, headers=headers)
            print(f"POST /anon-posts/: {post_resp.status_code}")
            
        else:
            print(f"\n=== LOGIN FAILED ===")

asyncio.run(test())
