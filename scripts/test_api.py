from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = "mongodb+srv://soulspace_user:WCXtXES9Hz4Xb2mA@soulspace-cluster.4ho75yb.mongodb.net/?retryWrites=true&w=majority&appName=soulspace-cluster"
DATABASE_NAME = "soulspace"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

db["reports"].delete_many({})
print("Đã xóa toàn bộ bản ghi trong collection reports.")