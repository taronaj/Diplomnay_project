from pydantic import BaseModel
import datetime

# Схема для создания комментария
class CreateComment(BaseModel):
    lesson_id: int
    content: str

# Схема для обновления комментария
class CommentUpdate(BaseModel):
    content: str

# Схема для ответа с данными комментария
class CommentResponse(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_deleted: bool

    class Config:
        from_attributes = True