from pydantic import BaseModel

class TopicStatItem(BaseModel):
    topic: str
    count: int