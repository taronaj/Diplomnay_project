from sqlalchemy.orm import Session
from db.models import Attendance, Homework
from db.postgres import engine


def get_attendance_rate(course_id: int, student_id: int):
    with Session(bind=engine) as db:
        attendance = db.query(Attendance).filter(Attendance.course_id == course_id,
                                                 Attendance.user_id == student_id).all()
        return attendance


def get_homework_rate(course_id: int, student_id: int):
    with Session(bind=engine) as db:
        homework = db.query(Homework).filter(Homework.course_id == course_id,
                                             Homework.student_id == student_id).all()
        return homework
