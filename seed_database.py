"""Initial data seeding for the diploma demo.

The seeder is idempotent: it creates missing records but does not overwrite
changes made later from the admin panel or dashboard.
"""
import datetime
import os

from db.models import (
    Application,
    Attendance,
    Course,
    CourseUser,
    Homework,
    Lesson,
    LessonMaterial,
    Payment,
    Role,
    Schedule,
    StudentPerformance,
    User,
    migrate_tables,
)
from db.postgres import SessionLocal
from utils.hash import hash_password
from core.materials import ensure_material_file, safe_material_filename


def _get_or_create_role(db, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _initial_password_for(username: str) -> str:
    if username == "admin":
        return os.getenv("INITIAL_ADMIN_PASSWORD", "change-me-admin")
    if username == "mentor":
        return os.getenv("INITIAL_MENTOR_PASSWORD", "change-me-mentor")
    return os.getenv("INITIAL_STUDENT_PASSWORD", "change-me-student")


def _get_or_create_user(db, username: str, full_name: str, role: Role) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    user = User(
        username=username,
        full_name=full_name,
        password=hash_password(_initial_password_for(username)),
        role_id=role.id,
        birth_date=datetime.datetime(2002, 1, 1),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _link_course_user(db, course_id: int, user_id: int) -> None:
    exists = db.query(CourseUser).filter(
        CourseUser.course_id == course_id,
        CourseUser.user_id == user_id,
    ).first()
    if not exists:
        db.add(CourseUser(course_id=course_id, user_id=user_id))
        db.commit()


def seed_demo_data() -> None:
    with SessionLocal() as db:
        admin_role = _get_or_create_role(db, "Администратор")
        mentor_role = _get_or_create_role(db, "Преподаватель")
        student_role = _get_or_create_role(db, "Студент")

        _get_or_create_user(db, "admin", "Администратор системы", admin_role)
        mentor = _get_or_create_user(db, "mentor", "Саидов Фарид", mentor_role)
        students = [
            _get_or_create_user(db, "student", "Каримова Мадина", student_role),
            _get_or_create_user(db, "student2", "Назаров Амир", student_role),
            _get_or_create_user(db, "student3", "Иброхимова Ситора", student_role),
            _get_or_create_user(db, "student4", "Юсупов Даврон", student_role),
        ]

        courses_seed = [
            ("Веб-разработка", 1200, "Создание современных веб-приложений и личных кабинетов"),
            ("Основы программирования", 1000, "Базовые алгоритмы, структуры данных и практика программирования"),
            ("Базы данных", 900, "Проектирование таблиц, SQL-запросы и работа с данными"),
            ("Искусственный интеллект", 1500, "Основы AI, аналитика учебного процесса и интеллектуальные сервисы"),
        ]
        for name, price, description in courses_seed:
            if not db.query(Course).filter(Course.name == name).first():
                db.add(Course(name=name, price=price, description=description))
        db.commit()

        courses = db.query(Course).filter(Course.deleted_at == None).order_by(Course.id.asc()).limit(4).all()
        lesson_titles = ["Введение", "Практическое занятие", "Домашняя работа", "Итоговый проект"]
        for course in courses:
            _link_course_user(db, course.id, mentor.id)
            for student in students:
                _link_course_user(db, course.id, student.id)
            if db.query(Lesson).filter(Lesson.course_id == course.id, Lesson.deleted_at == None).count() < 4:
                for title in lesson_titles:
                    full_title = f"{title}: {course.name}"
                    if not db.query(Lesson).filter(Lesson.course_id == course.id, Lesson.title == full_title).first():
                        db.add(Lesson(course_id=course.id, title=full_title, description=f"Тема урока по курсу {course.name}"))
        db.commit()

        lessons = db.query(Lesson).filter(Lesson.deleted_at == None).order_by(Lesson.id.asc()).limit(16).all()
        for lesson in lessons:
            if db.query(LessonMaterial).filter(LessonMaterial.lesson_id == lesson.id, LessonMaterial.deleted_at == None).count() < 2:
                for idx, (label, ext) in enumerate([("Конспект урока", ".txt"), ("Практическое задание", ".docx")], start=1):
                    filename = f"{label} - {lesson.title}{ext}"[:110]
                    if not db.query(LessonMaterial).filter(LessonMaterial.lesson_id == lesson.id, LessonMaterial.filename == filename).first():
                        db.add(LessonMaterial(
                            lesson_id=lesson.id,
                            filename=filename,
                            hashed_filename=safe_material_filename(lesson.id, idx, ext),
                            file_size_bytes=1,
                        ))
        db.commit()

        for material in db.query(LessonMaterial).filter(LessonMaterial.deleted_at == None).all():
            ensure_material_file(material)
        db.commit()

        for i, student in enumerate(students):
            if not courses:
                continue
            course = courses[i % len(courses)]
            lesson = next((item for item in lessons if item.course_id == course.id), None)
            if not lesson:
                continue
            if not db.query(Homework).filter(Homework.student_id == student.id, Homework.lesson_id == lesson.id).first():
                db.add(Homework(lesson_id=lesson.id, student_id=student.id, course_id=course.id, mentor_id=mentor.id, score=82 + i * 4, homework="Выполненное домашнее задание"))
            if not db.query(Attendance).filter(Attendance.user_id == student.id, Attendance.lesson_id == lesson.id).first():
                db.add(Attendance(lesson_id=lesson.id, user_id=student.id, course_id=course.id, attended=(i != 2), attendance_date=datetime.datetime.now() - datetime.timedelta(days=i)))
            if not db.query(StudentPerformance).filter(StudentPerformance.student_id == student.id, StudentPerformance.course_id == course.id).first():
                db.add(StudentPerformance(student_id=student.id, course_id=course.id, avg_score=82 + i * 4, attendance_rate=95 - i * 5))
        db.commit()

        if db.query(Schedule).count() < 4:
            for i, course in enumerate(courses[:4]):
                lesson = next((item for item in lessons if item.course_id == course.id), None)
                if lesson:
                    db.add(Schedule(course_id=course.id, lesson_id=lesson.id, mentor_id=mentor.id, scheduled_time=datetime.datetime.now() + datetime.timedelta(days=i + 1, hours=10)))
        if db.query(Application).count() < 4:
            for i in range(4):
                db.add(Application(full_name=f"Заявка студент {i + 1}", phone=f"+99290000000{i}", email=f"student{i + 1}@mail.com", course_id=courses[i % len(courses)].id if courses else None, status="new", source="Сайт", message="Хочу записаться на курс"))
        if db.query(Payment).count() < 4:
            for i, student in enumerate(students):
                db.add(Payment(user_id=student.id, course_id=courses[i % len(courses)].id if courses else None, amount=500 + i * 100, status="paid" if i % 2 == 0 else "pending", provider="Наличные", transaction_reference=f"PAY-{1000 + i}", paid_at=datetime.datetime.now() if i % 2 == 0 else None))
        db.commit()


if __name__ == "__main__":
    migrate_tables()
    seed_demo_data()
    print("Готово: начальные учебные данные сохранены в базе данных.")



