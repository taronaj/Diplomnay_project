from datetime import datetime

from pydantic import BaseModel


class AttendanceSchema(BaseModel):
    lesson_id: int
    user_id: int
    course_id: int
    attended: bool
    attendance_date: datetime
