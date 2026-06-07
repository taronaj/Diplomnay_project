from fastapi import HTTPException
from db.models import Homework, User
from pkg.repositories import homeworks as homework_repository
from schemas.homeworks import HomeworkSchema


def get_student_homeworks(user_id, homework_id):
    homework = homework_repository.get_homework_by_student(user_id, homework_id)
    return homework


def add_homework(user_id, homeworks: HomeworkSchema):
    role = homework_repository.get_user_role(user_id)
    if role != "mentor":
        raise HTTPException(status_code=403, detail="Only mentors can add homework")

    if not homework_repository.is_mentor_of_course(user_id, homeworks.lesson_id):
        raise HTTPException(status_code=403, detail="Only mentors of the course can grade students")

    h = Homework()
    h.course_id = homeworks.course_id
    h.lesson_id = homeworks.lesson_id
    h.student_id = homeworks.student_id
    h.homework = homeworks.homework
    h.score = homeworks.score
    h.deleted_at = None

    return homework_repository.create_homework(h)


def edit_homework(user_id, homework_id: int, score: float):
    role = homework_repository.get_user_role(user_id)
    if role != "mentor":
        raise HTTPException(status_code=403, detail="Only mentors can edit homework")

    homework = homework_repository.get_homework_by_id(homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    course_id = homework_repository.get_course_by_lesson(homework.lesson_id)
    if not course_id:
        raise HTTPException(status_code=404, detail="Course not found for this lesson")

    if not homework_repository.is_mentor_of_course(user_id, course_id):
        raise HTTPException(status_code=403, detail="Only mentors of the course can edit the homework grade")

    return homework_repository.update_homework(homework_id, score)


def remove_homework(user_id, homework_id: int):
    role = homework_repository.get_user_role(user_id)

    if role != "mentor":
        raise HTTPException(status_code=403, detail="Only mentors can delete homework")

    homework = homework_repository.get_homework_by_id(homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    course_id = homework_repository.get_course_by_lesson(homework.lesson_id)
    if not course_id:
        raise HTTPException(status_code=404, detail="Course not found for this lesson")

    if not homework_repository.is_mentor_of_course(user_id, course_id):
        raise HTTPException(status_code=403, detail="Only mentors of the course can delete the homework")

    return homework_repository.delete_homework(homework_id)



def soft_delete_homework(user_id, homework_id: int):
    role = homework_repository.get_user_role(user_id)

    if role != "mentor":
        raise HTTPException(status_code=403, detail="Only mentors can soft delete homework")

    homework = homework_repository.get_homework_by_id(homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    course_id = homework_repository.get_course_by_lesson(homework.lesson_id)
    if not course_id:
        raise HTTPException(status_code=404, detail="Course not found for this lesson")

    if not homework_repository.is_mentor_of_course(user_id, course_id):
        raise HTTPException(status_code=403, detail="Only mentors of the course can delete the homework")
    return homework_repository.soft_delete_homework(homework_id)