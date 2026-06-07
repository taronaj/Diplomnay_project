from fastapi import FastAPI

from pkg.controllers.ai import router as ai_router
from pkg.controllers.attendances import router as attendance_router
from pkg.controllers.auth import router as auth_router
from pkg.controllers.comments import router as comments_router
from pkg.controllers.course_controller import router as courses_router
from pkg.controllers.course_members import router as course_members_router
from pkg.controllers.event import router as event_router
from pkg.controllers.homeworks import router as homeworks_router
from pkg.controllers.lesson import router as lesson_router
from pkg.controllers.lesson_material import router as material_router
from pkg.controllers.student_performance import router as student_perf_router
from routers.files import router as files_router
from routers.frontend_api import router as frontend_router
from routers.health import router as health_router

API_ROUTERS = (
    health_router,
    frontend_router,
    files_router,
    auth_router,
    courses_router,
    lesson_router,
    homeworks_router,
    attendance_router,
    event_router,
    course_members_router,
    material_router,
    student_perf_router,
    comments_router,
    ai_router,
)


def include_api_routers(app: FastAPI) -> None:
    for router in API_ROUTERS:
        app.include_router(router)
