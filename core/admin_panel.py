from fastapi import FastAPI

from admin import (
    AdminAuth,
    ApplicationAdmin,
    AttendanceAdmin,
    CommentAdmin,
    CourseAdmin,
    CourseUserAdmin,
    DashboardAdmin,
    EventAdmin,
    HomeworkAdmin,
    LessonAdmin,
    LessonMaterialAdmin,
    LoginHistoryAdmin,
    MentorActivityAdmin,
    PaymentAdmin,
    RoleAdmin,
    ScheduleAdmin,
    StudentPerformanceAdmin,
    UserAdmin,
)
from configs.config import settings
from db.postgres import engine

ADMIN_VIEWS = (
    UserAdmin,
    RoleAdmin,
    CourseAdmin,
    LessonAdmin,
    LessonMaterialAdmin,
    CommentAdmin,
    HomeworkAdmin,
    AttendanceAdmin,
    StudentPerformanceAdmin,
    EventAdmin,
    LoginHistoryAdmin,
    MentorActivityAdmin,
    ScheduleAdmin,
    CourseUserAdmin,
    ApplicationAdmin,
    PaymentAdmin,
)


def register_admin_panel(app: FastAPI) -> None:
    admin = DashboardAdmin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=settings.auth.secret_key),
        title="Админ-панель",
        base_url="/admin",
        templates_dir="project/templates",
    )

    for view in ADMIN_VIEWS:
        admin.add_view(view)
