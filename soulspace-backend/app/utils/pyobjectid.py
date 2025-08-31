from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.str_schema(),
        ])