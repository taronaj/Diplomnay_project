from pydantic import BaseModel


class EventSchema(BaseModel):
    user_id: int
    event_type: str
    event_description: str
    related_id: int
