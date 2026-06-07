import datetime
from sqlalchemy.orm import Session
from db.postgres import engine
from db.models import Homework, CourseUser, Lesson, User, Role


def get_user_role(user_id: int):
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.id == user.role_id).first()
        return role.name


def get_homework_by_student(user_id: int, homework_id: int):
    with Session(bind=engine) as db:
        homework = (
            db.query(Homework)
            .filter(Homework.student_id == user_id, Homework.id == homework_id)
            .first()
        )

        if not homework:
            return {"error": "No homework found for this student with the given ID"}

        return {"homework": homework.homework}



def get_course_by_lesson(lesson_id: int):
    with Session(bind=engine) as db:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        return lesson.course_id if lesson else None


def is_mentor_of_course(mentor_id: int, course_id: int):
    with Session(bind=engine) as db:
        return db.query(CourseUser).filter(
            CourseUser.user_id == mentor_id,
            CourseUser.course_id == course_id
        ).first() is not None



def create_homework(homework: Homework):
    with Session(bind=engine) as db:
        db.add(homework)
        db.commit()
        db.refresh(homework)
        return homework.id


def get_homework_by_id(homework_id: int):
    with Session(bind=engine) as db:
        return db.query(Homework).filter(Homework.id == homework_id).first()


def update_homework(homework_id: int, score: float):
    with Session(bind=engine) as db:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        if homework:
            homework.score = score
            homework.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(homework)
            return homework.id
        return None


def delete_homework(homework_id: int):
    with Session(bind=engine) as db:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        if homework:
            db.delete(homework)
            db.commit()
            return homework.id
        return False


def soft_delete_homework(homework_id: int):
    with Session(bind=engine) as db:
        homework = db.query(Homework).filter(Homework.id == homework_id).first()
        if homework:
            homework.deleted_at = datetime.datetime.now()
            db.commit()
            return homework.id
        return False