from bson import ObjectId

def convert_objectid_to_str(obj):
    """
    Recursively convert all ObjectId in dict/list to string.
    """
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj
