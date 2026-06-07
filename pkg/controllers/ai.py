import json
import os
import re
from pathlib import Path
from urllib import request, error

from fastapi import APIRouter, HTTPException

from schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    HomeworkCheckRequest,
    HomeworkCheckResponse,
    TestCheckRequest,
    TestCheckResponse,
    TestGenerateRequest,
    TestGenerateResponse,
    TestQuestion,
)


router = APIRouter(prefix="/ai", tags=["ИИ-помощник"])


def load_env_key() -> str:
    """Read GEMINI_API_KEY from environment or local .env file."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _extract_json(text: str) -> dict | list | None:
    """Try to extract JSON from Gemini text response."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def _gemini_request(prompt: str, max_tokens: int = 1000) -> str | None:
    api_key = load_env_key()
    if not api_key:
        return None

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": max_tokens},
    }

    req = request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=25) as response:
            raw = json.loads(response.read().decode("utf-8"))
        parts = raw["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def local_fallback_answer(message: str, role: str) -> AIChatResponse:
    text = message.lower().strip()

    if "python" in text or "питон" in text:
        answer = "Python — язык программирования, который используется для backend-разработки, анализа данных и искусственного интеллекта."
    elif "fastapi" in text or "фастапи" in text:
        answer = "FastAPI — современный Python-фреймворк для создания быстрых REST API с автоматической Swagger-документацией."
    elif "база" in text or "sql" in text or "данн" in text:
        answer = "База данных хранит пользователей, курсы, уроки, материалы, оценки и посещаемость учебной платформы."
    elif "домаш" in text or "задан" in text:
        answer = "Для выполнения домашнего задания сначала изучите материал урока, затем выполните практическую часть и отправьте результат преподавателю."
    # elif "защит" in text or "диплом" in text:
        # answer = "На защите покажите вход в систему, роли пользователей, курсы, уроки, материалы, оценки, посещаемость и работу AI-помощника."
    else:
        answer = "AI-помощник готов ответить на ваш вопрос по учебным темам, программированию, материалам курса и домашним заданиям."

    return AIChatResponse(
        answer=answer,
        suggestions=["Проверь домашнее задание", "Составь тест по теме", "Объясни тему урока"],
        provider="local",
    )


def ask_gemini(message: str, role: str) -> AIChatResponse:
    prompt = (
        "Ты AI-помощник учебной платформы. Отвечай кратко, понятно и по-русски. "
        "Помогай студентам с учебными материалами, домашними заданиями, программированием, базами данных, "
        "FastAPI, Python. "
        f"Роль пользователя в системе: {role}.\n\nВопрос пользователя: {message}"
    )
    answer = _gemini_request(prompt, max_tokens=700)
    if not answer:
        return local_fallback_answer(message, role)
    return AIChatResponse(
        answer=answer,
        suggestions=["Проверь домашнее задание", "Составь тест по теме", "Объясни проще"],
        provider="gemini",
    )


def local_homework_check(payload: HomeworkCheckRequest) -> HomeworkCheckResponse:
    text = payload.homework_text.strip()
    words = len(text.split())
    score = 50
    if words >= 30:
        score += 15
    if words >= 70:
        score += 10
    if any(token in text.lower() for token in ["пример", "вывод", "потому", "следовательно", "алгоритм", "код"]):
        score += 15
    if len(text) > 500:
        score += 10
    score = min(score, 95)

    if score >= 85:
        level = "Отлично"
    elif score >= 70:
        level = "Хорошо"
    elif score >= 55:
        level = "Удовлетворительно"
    else:
        level = "Нужно доработать"

    return HomeworkCheckResponse(
        score=score,
        level=level,
        feedback=f"Домашнее задание по теме «{payload.lesson_title}» проверено. Ответ в целом соответствует теме, но можно усилить аргументацию и добавить больше конкретных примеров.",
        strengths=["Ответ относится к теме", "Есть попытка раскрыть основную идею"],
        mistakes=["Недостаточно подробное объяснение", "Мало практических примеров"],
        recommendations=["Добавить пример из урока", "Сделать вывод в конце", "Проверить оформление и термины"],
        provider="local",
    )


def gemini_homework_check(payload: HomeworkCheckRequest) -> HomeworkCheckResponse:
    prompt = f"""
Ты преподаватель учебной платформы. Проверь домашнее задание студента.
Тема урока: {payload.lesson_title}
Критерии: {payload.criteria}

Ответ студента:
{payload.homework_text}

Верни только JSON без markdown в таком формате:
{{
  "score": 0-100,
  "level": "Отлично/Хорошо/Удовлетворительно/Нужно доработать",
  "feedback": "краткий общий отзыв",
  "strengths": ["сильная сторона 1", "сильная сторона 2"],
  "mistakes": ["ошибка 1", "ошибка 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}}
"""
    raw = _gemini_request(prompt, max_tokens=900)
    parsed = _extract_json(raw or "")
    if not isinstance(parsed, dict):
        return local_homework_check(payload)
    try:
        return HomeworkCheckResponse(
            score=max(0, min(100, int(parsed.get("score", 0)))),
            level=str(parsed.get("level", "Проверено")),
            feedback=str(parsed.get("feedback", "Домашнее задание проверено.")),
            strengths=list(parsed.get("strengths", []))[:5],
            mistakes=list(parsed.get("mistakes", []))[:5],
            recommendations=list(parsed.get("recommendations", []))[:5],
            provider="gemini",
        )
    except (TypeError, ValueError):
        return local_homework_check(payload)


def local_generate_test(payload: TestGenerateRequest) -> TestGenerateResponse:
    topic = payload.topic.strip()
    questions = []
    templates = [
        (f"Что является основной идеей темы «{topic}»?", ["Понимание ключевых понятий", "Удаление базы данных", "Отключение сервера", "Случайный выбор"], "Понимание ключевых понятий"),
        (f"Что нужно сделать перед выполнением задания по теме «{topic}»?", ["Изучить материал урока", "Закрыть проект", "Удалить файлы", "Не читать условие"], "Изучить материал урока"),
        (f"Как лучше проверить результат по теме «{topic}»?", ["Сравнить с критериями", "Игнорировать ошибки", "Не запускать код", "Удалить ответ"], "Сравнить с критериями"),
        (f"Что помогает лучше понять тему «{topic}»?", ["Практический пример", "Отсутствие объяснения", "Случайный ответ", "Пустой файл"], "Практический пример"),
        (f"Как оформить ответ по теме «{topic}»?", ["Структурно и понятно", "Без логики", "Одним случайным словом", "Без проверки"], "Структурно и понятно"),
    ]
    for item in templates[: payload.questions_count]:
        questions.append(TestQuestion(question=item[0], options=item[1], correct_answer=item[2]))
    return TestGenerateResponse(topic=topic, questions=questions, provider="local")


def gemini_generate_test(payload: TestGenerateRequest) -> TestGenerateResponse:
    prompt = f"""
Составь учебный тест по теме: {payload.topic}.
Количество вопросов: {payload.questions_count}.
Каждый вопрос должен иметь 4 варианта ответа и один правильный ответ.
Верни только JSON без markdown в формате:
[
  {{"question":"...", "options":["A","B","C","D"], "correct_answer":"..."}}
]
"""
    raw = _gemini_request(prompt, max_tokens=1200)
    parsed = _extract_json(raw or "")
    if not isinstance(parsed, list):
        return local_generate_test(payload)
    questions = []
    for item in parsed[: payload.questions_count]:
        try:
            options = list(item.get("options", []))[:4]
            correct = str(item.get("correct_answer", ""))
            if len(options) >= 2 and correct:
                questions.append(TestQuestion(question=str(item.get("question", "Вопрос")), options=options, correct_answer=correct))
        except (AttributeError, TypeError):
            continue
    if not questions:
        return local_generate_test(payload)
    return TestGenerateResponse(topic=payload.topic, questions=questions, provider="gemini")


@router.post("/chat", response_model=AIChatResponse)
def chat_with_ai(payload: AIChatRequest):
    return ask_gemini(payload.message, payload.role)


@router.post("/homework/check", response_model=HomeworkCheckResponse)
def check_homework_with_ai(payload: HomeworkCheckRequest):
    return gemini_homework_check(payload)


@router.post("/test/generate", response_model=TestGenerateResponse)
def generate_test_with_ai(payload: TestGenerateRequest):
    return gemini_generate_test(payload)


@router.post("/test/check", response_model=TestCheckResponse)
def check_test(payload: TestCheckRequest):
    total = min(len(payload.answers), len(payload.correct_answers))
    score = sum(1 for i in range(total) if payload.answers[i].strip() == payload.correct_answers[i].strip())
    percent = round((score * 100 / total), 2) if total else 0
    if percent >= 85:
        feedback = "Отличный результат. Тема хорошо усвоена."
    elif percent >= 60:
        feedback = "Хороший результат, но некоторые вопросы стоит повторить."
    else:
        feedback = "Рекомендуется повторить тему и пройти тест ещё раз."
    return TestCheckResponse(score=score, total=total, percent=percent, feedback=feedback)





