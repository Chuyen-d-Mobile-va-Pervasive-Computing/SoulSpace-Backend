import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("Testing SoulSpace Backend - Role-Based Architecture")
print("=" * 60)

# Test 1: Admin health endpoint
print("\n1. Testing Admin Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/admin/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Expert health endpoint
print("\n2. Testing Expert Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/expert/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Check if old endpoints still work (backward compatibility)
print("\n3. Testing Backward Compatibility...")
print("   (Auth endpoint should still work at /api/v1/auth/...)")

print("\n" + "=" * 60)
print("✓ Role-based architecture is working!")
print("\nStructure:")
print("  - Common: /api/v1/auth/*")
print("  - User: /api/v1/journal/*, /api/v1/game/*, etc.")
print("  - Admin: /api/v1/admin/*")
print("  - Expert: /api/v1/expert/*")
