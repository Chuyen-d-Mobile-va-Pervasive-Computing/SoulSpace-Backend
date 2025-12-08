import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        # Login admin
        admin = {"email": "admin@gmail.com", "password": "Admin@123"}
        login = await client.post("http://127.0.0.1:8000/api/v1/auth/login", json=admin)
        data = login.json()
        print(f"Login status: {login.status_code}")
        print(f"Role: {data.get('role')}")
        token = data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n=== TEST ADMIN APIs ===\n")
        
        # GET APIs
        apis = [
            ("GET", "/admin/posts"),
            ("GET", "/admin/comments"),
            ("GET", "/admin/reports"),
            ("GET", "/admin/expert-articles/pending"),
        ]
        
        for method, path in apis:
            resp = await client.get(f"http://127.0.0.1:8000/api/v1{path}", headers=headers)
            print(f"{method} {path}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   Error: {resp.text[:200]}")

asyncio.run(test())
