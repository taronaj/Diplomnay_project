from pydantic import BaseModel, condecimal
from typing import Optional


class HomeworkSchema(BaseModel):
    course_id: int
    lesson_id: int
    student_id: int
    homework: Optional[str] = None
    score: condecimal(max_digits=5, decimal_places=2)


class HomeworkUpdateSchema(BaseModel):
    score: condecimal(max_digits=5, decimal_places=2)


class HomeworkResponseSchema(HomeworkSchema):
    id: int
    mentor_id: int
    homework: Optional[str] = None

    class Config:
        from_attributes = True
