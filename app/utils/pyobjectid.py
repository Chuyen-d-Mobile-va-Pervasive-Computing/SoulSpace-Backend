from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, CoreSchema

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        
        def validate_from_str(value: str) -> ObjectId:
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(
                pattern=r"^[0-9a-fA-F]{24}$"
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(validate_from_str),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance)
            ),
        )