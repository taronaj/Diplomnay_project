from pydantic import BaseModel


class CourseMembers(BaseModel):
    member_id: int
