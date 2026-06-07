from fastapi.testclient import TestClient

from main_admin import app


client = TestClient(app)


def test_ai_homework_check():
    response = client.post(
        "/ai/homework/check",
        json={
            "lesson_title": "Основы Python",
            "homework_text": "Python используется для backend разработки. В ответе приведён пример и сделан вывод.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "feedback" in data


def test_ai_test_generate_and_check():
    response = client.post("/ai/test/generate", json={"topic": "FastAPI", "questions_count": 3})
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) >= 1

    correct = [item["correct_answer"] for item in data["questions"]]
    check = client.post(
        "/ai/test/check",
        json={"topic": "FastAPI", "answers": correct, "correct_answers": correct},
    )
    assert check.status_code == 200
    assert check.json()["percent"] == 100
