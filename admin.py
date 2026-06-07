try:
    import bcrypt
except ImportError:
    bcrypt = None
from decimal import Decimal

import hashlib

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend, login_required
from starlette.responses import Response

from db.models import (
    Application,
    Attendance,
    Comment,
    Course,
    CourseUser,
    Event,
    Homework,
    Lesson,
    LessonMaterial,
    Payment,
    Role,
    Schedule,
    StudentPerformance,
    User,
)
from db.postgres import SessionLocal
from pkg.services import event as event_service


APPLICATION_STATUS_LABELS = {
    "new": "Новая",
    "in_review": "В обработке",
    "approved": "Одобрена",
    "rejected": "Отклонена",
}

PAYMENT_STATUS_LABELS = {
    "pending": "Ожидает",
    "paid": "Оплачено",
    "failed": "Ошибка",
    "refunded": "Возврат",
}


def _format_datetime(value):
    if value is None:
        return "-"
    return value.strftime("%d.%m.%Y %H:%M")


def _format_money(amount, currency="TJS"):
    if amount is None:
        return "-"
    value = Decimal(amount)
    return f"{value:,.2f} {currency}".replace(",", " ")


def get_dashboard_context():
    with SessionLocal() as db:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_courses = db.query(func.count(Course.id)).filter(Course.deleted_at == None).scalar() or 0
        total_lessons = db.query(func.count(Lesson.id)).filter(Lesson.deleted_at == None).scalar() or 0
        total_applications = db.query(func.count(Application.id)).scalar() or 0
        total_payments = db.query(func.count(Payment.id)).scalar() or 0
        paid_total = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "paid").scalar() or 0
        new_applications = db.query(func.count(Application.id)).filter(Application.status == "new").scalar() or 0
        upcoming_schedule = (
            db.query(Schedule)
            .order_by(Schedule.scheduled_time.asc())
            .limit(6)
            .all()
        )
        recent_events = (
            db.query(Event)
            .filter(Event.deleted_at == None)
            .order_by(Event.created_at.desc())
            .limit(6)
            .all()
        )
        recent_applications = (
            db.query(Application)
            .order_by(Application.created_at.desc())
            .limit(6)
            .all()
        )
        recent_payments = (
            db.query(Payment)
            .order_by(Payment.created_at.desc())
            .limit(6)
            .all()
        )

    return {
        "title": "Панель управления",
        "subtitle": "Статистика, заявки, оплаты и расписание",
        "stats": [
            {"label": "Пользователи", "value": total_users, "icon": "fa-solid fa-users", "tone": "emerald"},
            {"label": "Курсы", "value": total_courses, "icon": "fa-solid fa-book", "tone": "blue"},
            {"label": "Уроки", "value": total_lessons, "icon": "fa-solid fa-chalkboard-user", "tone": "amber"},
            {"label": "Новые заявки", "value": new_applications, "icon": "fa-solid fa-inbox", "tone": "violet"},
        ],
        "finance": {
            "payments_count": total_payments,
            "revenue": _format_money(paid_total),
        },
        "recent_events": recent_events,
        "recent_applications": recent_applications,
        "recent_payments": recent_payments,
        "upcoming_schedule": upcoming_schedule,
        "application_status_labels": APPLICATION_STATUS_LABELS,
        "payment_status_labels": PAYMENT_STATUS_LABELS,
        "format_datetime": _format_datetime,
        "format_money": _format_money,
        "applications_count": total_applications,
    }


class DashboardAdmin(Admin):
    @login_required
    async def index(self, request: Request) -> Response:
        context = get_dashboard_context()
        return await self.templates.TemplateResponse(request, "sqladmin/index.html", context)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

            if not username or not password:
                return False

            with SessionLocal() as db:
                user = db.query(User).filter(User.username == username).first()

                if not user:
                    return False

                if not self.verify_password(password, user.password):
                    return False

                role = db.query(Role).filter(Role.id == user.role_id).first()
                role_name = (role.name if role else "").lower()
                if not any(word in role_name for word in ["admin", "администратор"]):
                    return False

                event_service.log_event(
                    user_id=user.id,
                    event_type="admin_sign_in",
                    event_description=f"Администратор {user.username} вошел в админ-панель",
                    related_id=user.id,
                )

                request.session.update({
                    "user_id": user.id,
                    "username": user.username,
                    "role_id": user.role_id
                })
                return True

        except SQLAlchemyError:
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("user_id")
        if not user_id:
            return False

        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            role = db.query(Role).filter(Role.id == user.role_id).first()
            role_name = (role.name if role else "").lower()
            return any(word in role_name for word in ["admin", "администратор"])

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            if hashed_password.startswith("sha256$"):
                _, salt, digest = hashed_password.split("$", 2)
                return hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest() == digest
            if bcrypt and hashed_password.startswith("$2b$"):
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    hashed_password.encode("utf-8")
                )
            return plain_password == hashed_password
        except (ValueError, TypeError):
            return False


class BaseAdmin(ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 20
    page_size_options = [10, 20, 50, 100]
    save_as = True
    save_as_continue = False


class UserAdmin(BaseAdmin, model=User):
    column_list = [User.id, User.full_name, User.username, User.role_id, User.created_at]
    column_searchable_list = [User.full_name, User.username]
    column_sortable_list = [User.id, User.full_name, User.created_at]
    column_labels = {
        User.id: "ID",
        User.full_name: "ФИО",
        User.username: "Логин",
        User.password: "Пароль",
        User.role_id: "Роль",
        User.created_at: "Дата регистрации"
    }
    column_details_exclude_list = [User.password]
    form_excluded_columns = [User.password]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"


class RoleAdmin(BaseAdmin, model=Role):
    column_list = [Role.id, Role.name]
    column_searchable_list = [Role.name]
    column_labels = {
        Role.id: "ID",
        Role.name: "Название роли"
    }
    name = "Роль"
    name_plural = "Роли"
    icon = "fa-solid fa-tags"


class CourseAdmin(BaseAdmin, model=Course):
    column_list = [Course.id, Course.name, Course.price, Course.created_at]
    column_searchable_list = [Course.name]
    column_sortable_list = [Course.id, Course.name, Course.price]
    column_labels = {
        Course.id: "ID",
        Course.name: "Название курса",
        Course.price: "Цена (₸)",
        Course.description: "Описание",
        Course.created_at: "Дата создания"
    }
    form_columns = [Course.name, Course.price, Course.description]
    name = "Курс"
    name_plural = "Курсы"
    icon = "fa-solid fa-book"


class LessonAdmin(BaseAdmin, model=Lesson):
    column_list = [Lesson.id, Lesson.title, Lesson.course_id, Lesson.created_at]
    column_searchable_list = [Lesson.title]
    column_labels = {
        Lesson.id: "ID",
        Lesson.title: "Название урока",
        Lesson.course_id: "Курс",
        Lesson.description: "Описание",
        Lesson.created_at: "Дата создания"
    }
    name = "Урок"
    name_plural = "Уроки"
    icon = "fa-solid fa-chalkboard-user"


class LessonMaterialAdmin(BaseAdmin, model=LessonMaterial):
    column_list = [LessonMaterial.id, LessonMaterial.filename, LessonMaterial.lesson_id, LessonMaterial.file_size_bytes, LessonMaterial.created_at]
    column_searchable_list = [LessonMaterial.filename]
    column_labels = {
        LessonMaterial.id: "ID",
        LessonMaterial.filename: "Имя файла",
        LessonMaterial.lesson_id: "Урок",
        LessonMaterial.file_size_bytes: "Размер (байт)",
        LessonMaterial.created_at: "Дата загрузки"
    }
    name = "Материал"
    name_plural = "Материалы уроков"
    icon = "fa-solid fa-paperclip"


class CommentAdmin(BaseAdmin, model=Comment):
    column_list = [Comment.id, Comment.content, Comment.user_id, Comment.lesson_id, Comment.created_at]
    column_searchable_list = [Comment.content]
    column_labels = {
        Comment.id: "ID",
        Comment.content: "Комментарий",
        Comment.user_id: "Пользователь",
        Comment.lesson_id: "Урок",
        Comment.created_at: "Дата"
    }
    name = "Комментарий"
    name_plural = "Комментарии"
    icon = "fa-solid fa-comments"


class HomeworkAdmin(BaseAdmin, model=Homework):
    column_list = [Homework.id, Homework.student_id, Homework.lesson_id, Homework.score, Homework.submission_date]
    column_sortable_list = [Homework.score, Homework.submission_date]
    column_labels = {
        Homework.id: "ID",
        Homework.student_id: "Студент",
        Homework.lesson_id: "Урок",
        Homework.score: "Оценка",
        Homework.submission_date: "Дата сдачи",
        Homework.homework: "Домашнее задание"
    }
    name = "Домашнее задание"
    name_plural = "Домашние задания"
    icon = "fa-solid fa-home"


class AttendanceAdmin(BaseAdmin, model=Attendance):
    column_list = [Attendance.id, Attendance.user_id, Attendance.lesson_id, Attendance.attended, Attendance.attendance_date]
    column_sortable_list = [Attendance.attendance_date]
    column_labels = {
        Attendance.id: "ID",
        Attendance.user_id: "Студент",
        Attendance.lesson_id: "Урок",
        Attendance.attended: "Присутствовал",
        Attendance.attendance_date: "Дата занятия"
    }
    name = "Посещаемость"
    name_plural = "Посещаемость"
    icon = "fa-solid fa-calendar-check"


class StudentPerformanceAdmin(BaseAdmin, model=StudentPerformance):
    column_list = [StudentPerformance.id, StudentPerformance.student_id, StudentPerformance.course_id, StudentPerformance.avg_score, StudentPerformance.attendance_rate]
    column_labels = {
        StudentPerformance.id: "ID",
        StudentPerformance.student_id: "Студент",
        StudentPerformance.course_id: "Курс",
        StudentPerformance.avg_score: "Средний балл",
        StudentPerformance.attendance_rate: "Посещаемость (%)"
    }
    name = "Успеваемость"
    name_plural = "Успеваемость"
    icon = "fa-solid fa-chart-line"


class EventAdmin(BaseAdmin, model=Event):
    column_list = [Event.id, Event.event_type, Event.user_id, Event.created_at]
    column_searchable_list = [Event.event_type, Event.event_description]
    column_sortable_list = [Event.created_at]
    column_labels = {
        Event.id: "ID",
        Event.event_type: "Тип события",
        Event.event_description: "Описание",
        Event.user_id: "Пользователь",
        Event.related_id: "Объект",
        Event.created_at: "Дата"
    }
    name = "Событие"
    name_plural = "Лог событий"
    icon = "fa-solid fa-bell"


class LoginHistoryAdmin(BaseAdmin, model=Event):
    column_list = [Event.id, Event.user_id, Event.event_type, Event.event_description, Event.created_at]
    column_searchable_list = [Event.event_type, Event.event_description]
    column_sortable_list = [Event.created_at]
    column_labels = {
        Event.id: "ID",
        Event.user_id: "Пользователь",
        Event.event_type: "Тип входа",
        Event.event_description: "Описание",
        Event.created_at: "Дата",
    }
    column_formatters = {
        Event.created_at: lambda model, _: _format_datetime(model.created_at),
    }
    can_create = False
    can_edit = False
    can_delete = False
    name = "История входов"
    name_plural = "История входов"
    icon = "fa-solid fa-right-to-bracket"

    def list_query(self, request: Request):
        return select(Event).where(
            Event.deleted_at == None,
            Event.event_type.in_(["user_sign_in", "admin_sign_in"]),
        )

    def count_query(self, request: Request):
        return select(Event).where(
            Event.deleted_at == None,
            Event.event_type.in_(["user_sign_in", "admin_sign_in"]),
        )


class MentorActivityAdmin(BaseAdmin, model=Event):
    column_list = [Event.id, Event.user_id, Event.event_type, Event.event_description, Event.related_id, Event.created_at]
    column_searchable_list = [Event.event_type, Event.event_description]
    column_sortable_list = [Event.created_at]
    column_labels = {
        Event.id: "ID",
        Event.user_id: "Ментор",
        Event.event_type: "Действие",
        Event.event_description: "Описание",
        Event.related_id: "Объект",
        Event.created_at: "Дата",
    }
    column_formatters = {
        Event.created_at: lambda model, _: _format_datetime(model.created_at),
    }
    can_create = False
    can_edit = False
    can_delete = False
    name = "Действие ментора"
    name_plural = "Действия менторов"
    icon = "fa-solid fa-user-pen"

    def list_query(self, request: Request):
        mentor_role_ids = select(Role.id).where(Role.name.in_(["Преподаватель", "Mentor", "Teacher", "mentor", "teacher"]))
        mentor_ids = select(User.id).where(User.role_id.in_(mentor_role_ids))
        return select(Event).where(
            Event.deleted_at == None,
            Event.user_id.in_(mentor_ids),
        )

    def count_query(self, request: Request):
        mentor_role_ids = select(Role.id).where(Role.name.in_(["Преподаватель", "Mentor", "Teacher", "mentor", "teacher"]))
        mentor_ids = select(User.id).where(User.role_id.in_(mentor_role_ids))
        return select(Event).where(
            Event.deleted_at == None,
            Event.user_id.in_(mentor_ids),
        )


class ScheduleAdmin(BaseAdmin, model=Schedule):
    column_list = [Schedule.id, Schedule.course_id, Schedule.lesson_id, Schedule.mentor_id, Schedule.scheduled_time]
    column_sortable_list = [Schedule.scheduled_time]
    column_labels = {
        Schedule.id: "ID",
        Schedule.course_id: "Курс",
        Schedule.lesson_id: "Урок",
        Schedule.mentor_id: "Преподаватель",
        Schedule.scheduled_time: "Время занятия"
    }
    name = "Расписание"
    name_plural = "Расписание"
    icon = "fa-solid fa-calendar-alt"


class CourseUserAdmin(BaseAdmin, model=CourseUser):
    column_list = [CourseUser.course_id, CourseUser.user_id]
    column_labels = {
        CourseUser.course_id: "Курс",
        CourseUser.user_id: "Пользователь"
    }
    name = "Участник"
    name_plural = "Участники курсов"
    icon = "fa-solid fa-users"


class ApplicationAdmin(BaseAdmin, model=Application):
    column_list = [Application.id, Application.full_name, Application.phone, Application.course_id, Application.status, Application.created_at]
    column_searchable_list = [Application.full_name, Application.phone, Application.email, Application.message]
    column_sortable_list = [Application.created_at]
    column_labels = {
        Application.id: "ID",
        Application.full_name: "Имя",
        Application.phone: "Телефон",
        Application.email: "Email",
        Application.course_id: "Курс",
        Application.status: "Статус",
        Application.source: "Источник",
        Application.message: "Комментарий",
        Application.created_at: "Создано",
        Application.updated_at: "Обновлено",
    }
    column_formatters = {
        Application.status: lambda model, _: APPLICATION_STATUS_LABELS.get(model.status, model.status),
        Application.created_at: lambda model, _: _format_datetime(model.created_at),
    }
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-inbox"


class PaymentAdmin(BaseAdmin, model=Payment):
    column_list = [Payment.id, Payment.user_id, Payment.course_id, Payment.amount, Payment.provider, Payment.status, Payment.paid_at]
    column_searchable_list = [Payment.provider, Payment.transaction_reference, Payment.notes]
    column_sortable_list = [Payment.created_at, Payment.paid_at]
    column_labels = {
        Payment.id: "ID",
        Payment.user_id: "Пользователь",
        Payment.course_id: "Курс",
        Payment.application_id: "Заявка",
        Payment.amount: "Сумма",
        Payment.currency: "Валюта",
        Payment.status: "Статус",
        Payment.provider: "Провайдер",
        Payment.transaction_reference: "Транзакция",
        Payment.paid_at: "Оплачено",
        Payment.notes: "Комментарий",
        Payment.created_at: "Создано",
        Payment.updated_at: "Обновлено",
    }
    column_formatters = {
        Payment.amount: lambda model, _: _format_money(model.amount, model.currency),
        Payment.status: lambda model, _: PAYMENT_STATUS_LABELS.get(model.status, model.status),
        Payment.paid_at: lambda model, _: _format_datetime(model.paid_at),
    }
    name = "Оплата"
    name_plural = "Оплаты"
    icon = "fa-solid fa-credit-card"
