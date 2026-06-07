from pydantic import BaseModel, Field


class CourseSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    price: int = Field(default=0, ge=0)
    description: str = Field(..., min_length=3, max_length=2000)


class CourseRead(BaseModel):
    id: int
    name: str
    price: int | None = 0
    description: str | None = ""


class CourseListResponse(BaseModel):
    courses: list[CourseRead]


class MessageResponse(BaseModel):
    message: str
