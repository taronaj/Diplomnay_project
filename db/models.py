import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, DECIMAL
from sqlalchemy.exc import SQLAlchemyError

from db.postgres import engine


class Base(DeclarativeBase):
    pass


# Таблица пользователей (студенты, родители, преподаватели, администраторы)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    full_name = Column(String)  # Полное имя
    username = Column(String, unique=True, nullable=False, index=True)  # Логин пользователя
    password = Column(String, nullable=False)  # Пароль (должен быть хеширован)
    birth_date = Column(DateTime)  # Дата рождения
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)  # ID роли (Один пользователь - одна роль)
    created_at = Column(DateTime, default=datetime.datetime.now)  # Дата создания аккаунта


# Таблица ролей (Студент, Преподаватель, Администратор, Родитель)
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Название роли


# Таблица курсов (каждый курс может содержать несколько уроков)
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Название курса
    price = Column(Integer)  # Стоимость курса
    description = Column(Text, nullable=False)  # Описание курса
    created_at = Column(DateTime, default=datetime.datetime.now)  # Дата создания
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Дата обновления
    deleted_at = Column(DateTime, nullable=True)  # Дата удаления


# Таблица связи пользователей и курсов (многие ко многим: кто записан на курс)
class CourseUser(Base):
    __tablename__ = "course_users"
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True, index=True)  # ID курса
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)  # ID пользователя


# Таблица уроков (содержит информацию об уроках внутри курса)
class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)  # ID курса, к которому принадлежит урок
    title = Column(String, nullable=False)  # Название урока
    description = Column(Text)  # Описание урока
    created_at = Column(DateTime, default=datetime.datetime.now)  # Дата создания
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Дата обновления
    deleted_at = Column(DateTime, nullable=True)  # Дата удаления


# Таблица материалов для уроков
class LessonMaterial(Base):
    __tablename__ = "lesson_materials"
    id = Column(Integer, primary_key=True)
    # ID урока, к которому принадлежит материал
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)
    filename = Column(String)  # имя файла
    hashed_filename = Column(String)  # хэшированное имя файла
    file_size_bytes = Column(Integer)  # размер файла
    created_at = Column(DateTime, default=datetime.datetime.now)  # Двта создания
    updated_at = Column(DateTime, onupdate=datetime.datetime.now)  # Дата обновления
    deleted_at = Column(DateTime, nullable=True)  # Дата удаления


# Таблица комментариев к урокам
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)  # ID урока, к которому принадлежит коммент
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # ID пользователя, которому принадлежит коммент
    content = Column(Text, nullable=False)  # Текст комментария
    created_at = Column(DateTime, default=datetime.datetime.now)  # Двта создания
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Дата обновления
    deleted_at = Column(DateTime, nullable=True)  # Дата удаления


# Таблица домашних заданий (содержит оценки за выполненные задания)
class Homework(Base):
    __tablename__ = "homeworks"  # Укажите имя таблицы в базе данных
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)  # ID урока
    student_id = Column(Integer, ForeignKey("users.id"), index=True)  # ID студента
    course_id = Column(Integer, ForeignKey("courses.id"))
    score = Column(DECIMAL(5, 2))  # Оценка за задание (0.00 - 100.00)
    submission_date = Column(DateTime, default=datetime.datetime.now)
    mentor_id = Column(Integer, ForeignKey("users.id"), index=True)
    deleted_at = Column(DateTime, nullable=True, default=None)
    homework = Column(String, nullable=True)



# Таблица посещаемости (фиксирует, кто посетил урок)
class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)  # ID урока
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # ID студента
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)  # ID курса
    attended = Column(Boolean)  # Был ли студент на занятии (True = Да, False = Нет)
    attendance_date = Column(DateTime, default=datetime.datetime.now)  # Дата посещения


# Аналитика успеваемости студента
class StudentPerformance(Base):
    __tablename__ = "student_performances"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)  # ID студента
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)  # ID курса
    avg_score = Column(DECIMAL(5, 2))  # Средний балл (0.00 - 100.00)
    attendance_rate = Column(DECIMAL(5, 2))  # Процент посещаемости (0.00 - 100.00)


# Лента событий (лог действий: обновления оценок, новые уроки и т. д.) - *** only admin ***
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    # ID пользователя, связанного с событием
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    # Тип события ('обновление оценки', 'новый урок')
    event_type = Column(String)
    event_description = Column(Text)  # Описание события
    # ID связанного объекта (урока, курса, комментария и т. д.)
    related_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now)  # Дата события
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Дата обновления
    deleted_at = Column(DateTime, nullable=True)  # Дата удаления


# Таблица расписания (расписание занятий для студентов и преподавателей)
class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)  # ID курса
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)  # ID урока
    mentor_id = Column(Integer, ForeignKey("users.id"), index=True)  # ID преподавателя
    scheduled_time = Column(DateTime, nullable=False)  # Дата и время занятия


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    status = Column(String, nullable=False, default="new")
    source = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="TJS")
    status = Column(String, nullable=False, default="pending")
    provider = Column(String, nullable=True)
    transaction_reference = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


def migrate_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Ошибка во время миграции: {exc}") from exc
