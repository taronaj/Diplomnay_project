from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    role: str = "student"


class AIChatResponse(BaseModel):
    answer: str
    suggestions: list[str] = []
    provider: str = "gemini"



class HomeworkCheckRequest(BaseModel):
    homework_text: str = Field(..., min_length=5, max_length=5000)
    lesson_title: str = Field(default="Учебная тема", max_length=200)
    criteria: str = Field(default="полнота ответа, правильность, логика, оформление", max_length=500)
    role: str = "student"


class HomeworkCheckResponse(BaseModel):
    score: int
    level: str
    feedback: str
    strengths: list[str] = []
    mistakes: list[str] = []
    recommendations: list[str] = []
    provider: str = "gemini"


class TestGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    questions_count: int = Field(default=5, ge=1, le=10)
    role: str = "student"


class TestQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str


class TestGenerateResponse(BaseModel):
    topic: str
    questions: list[TestQuestion]
    provider: str = "gemini"


class TestCheckRequest(BaseModel):
    topic: str = Field(default="Тест", max_length=200)
    answers: list[str] = []
    correct_answers: list[str] = []


class TestCheckResponse(BaseModel):
    score: int
    total: int
    percent: float
    feedback: str
