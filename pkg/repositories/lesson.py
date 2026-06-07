import datetime

from sqlalchemy.orm import Session
from db.postgres import engine
from db.models import Lesson, Course, CourseUser
from schemas.lesson import LessonSchema


def get_lesson(course_id: int):
    with Session(bind=engine) as db:
        db_lessons = db.query(Lesson).filter(
            Lesson.course_id == course_id,
            Lesson.deleted_at == None
        ).all()

    return db_lessons


def get_lesson_by_id(course_id: int, lesson_id: int):
    with Session(bind=engine) as db:
        db_lesson = db.query(Lesson).filter(
            Lesson.course_id == course_id,
            Lesson.id == lesson_id,
            Lesson.deleted_at == None
        ).first()

    return db_lesson


def create_lesson(lesson: Lesson):
    with Session(bind=engine) as db:
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        return lesson.id


def update_lesson(course_id: int, lesson_id: int, lesson: LessonSchema):
    with Session(bind=engine) as db:
        db_lesson = db.query(Lesson).filter(
            Lesson.id == lesson_id,
            Lesson.course_id == course_id,
        ).first()

        if not db_lesson:
            return None

        db_lesson.title = lesson.title
        db_lesson.description = lesson.description

        db.commit()

        return db_lesson


def delete_lesson(course_id: int, lesson_id: int):
    with Session(bind=engine) as db:
        db_lesson = db.query(Lesson).filter(
            Lesson.id == lesson_id,
            Lesson.course_id == course_id,
        ).first()

        if not db_lesson:
            return None

        db_lesson.deleted_at = datetime.datetime.now()

        db.commit()

        return db_lesson


def is_course_exists(course_id: int):
    with Session(bind=engine) as db:
        count = db.query(Course).filter(
            Course.id == course_id,
            Course.deleted_at == None
        ).count()

    return count > 0


def is_user_has_access_to_lesson(user_id: int, course_id: int):
    with Session(bind=engine) as db:
        count = db.query(CourseUser).filter(
            CourseUser.user_id == user_id,
            CourseUser.course_id == course_id
        ).count()

        return count > 0
