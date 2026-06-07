from fastapi import HTTPException
from db.models import Lesson
from pkg.repositories import lesson as lesson_repository
from pkg.repositories import user as user_repository
from schemas.lesson import LessonSchema


def is_admin_or_mentor(user_id: int) -> bool:
    user = user_repository.get_user_by_id(user_id)
    if not user:
        return False

    role_name = user_repository.get_user_role(user_id)
    return role_name in ["admin", "mentor"]


def is_user_has_access_to_lesson(user_id: int, course_id: int):
    return lesson_repository.is_user_has_access_to_lesson(
        user_id, course_id)


def get_lesson(course_id: int):
    lessons = lesson_repository.get_lesson(course_id)
    return lessons


def get_lesson_by_id(course_id: int, lesson_id: int):
    lesson = lesson_repository.get_lesson_by_id(course_id, lesson_id)
    return lesson


def create_lesson(course_id: int, lesson: LessonSchema):
    l = Lesson()
    l.title = lesson.title
    l.description = lesson.description
    l.course_id = course_id

    return lesson_repository.create_lesson(l)


def update_lesson(course_id: int, lesson_id: int, lesson: LessonSchema):
    return lesson_repository.update_lesson(course_id, lesson_id, lesson)


def delete_lesson(course_id: int, lesson_id: int):
    return lesson_repository.delete_lesson(course_id, lesson_id)


def is_course_exists(course_id: int):
    return lesson_repository.is_course_exists(course_id)
