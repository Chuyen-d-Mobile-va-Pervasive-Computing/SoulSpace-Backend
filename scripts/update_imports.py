import re
import os

# Define the root path
root_path = r"D:\SE405\SoulSpace-Backend\app"

# Define replacement patterns for routers
router_patterns = [
    (r'from app\.services\.(\w+_service) import', r'from app.services.user.\1 import'),
    (r'from app\.schemas\.(\w+_schema) import', r'from app.schemas.user.\1 import'),
]

# Define replacement patterns for services
service_patterns = [
    (r'from app\.schemas\.(\w+_schema) import', r'from app.schemas.user.\1 import'),
]

# Update user routers
router_files = [
    "api/user/anon_comment_router.py",
    "api/user/anon_like_router.py",
    "api/user/anon_post_router.py",
    "api/user/badge_router.py",
    "api/user/game_router.py",
    "api/user/journal_router.py",
    "api/user/reminder_router.py",
    "api/user/test_router.py",
    "api/user/user_tree_router.py",
]

for file_path in router_files:
    full_path = os.path.join(root_path, file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply replacements
        for pattern, replacement in router_patterns:
            content = re.sub(pattern, replacement, content)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")

# Update user services
service_files = [
    "services/user/anon_comment_service.py",
    "services/user/anon_like_service.py",
    "services/user/anon_post_service.py",
    "services/user/badge_service.py",
    "services/user/game_service.py",
    "services/user/journal_service.py",
    "services/user/reminder_service.py",
    "services/user/test_service.py",
    "services/user/user_test_result_service.py",
    "services/user/user_tree_service.py",
]

for file_path in service_files:
    full_path = os.path.join(root_path, file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply replacements
        for pattern, replacement in service_patterns:
            content = re.sub(pattern, replacement, content)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")

print("All imports updated successfully!")
