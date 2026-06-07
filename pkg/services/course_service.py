import datetime

from db.models import Course as CourseModel
from pkg.repositories import course_repository
from pkg.services import user
from schemas.course_schemas import CourseSchema


def get_courses() -> list[dict]:
    return course_repository.get_all()


def create_course(user_id: int, course_schema: CourseSchema) -> dict:
    user_permission = user.admin_or_mentor_permission_check(user_id)
    if user_permission:
        return user_permission
    course = CourseModel(
        name=course_schema.name,
        description=course_schema.description,
        price=course_schema.price,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    return course_repository.create(course)


def update_course(user_id: int, course_schema: CourseSchema, course_id: int) -> dict:
    user_permission = user.admin_or_mentor_permission_check(user_id)
    if user_permission:
        return user_permission
    if not course_repository.get_by_id(course_id):
        return {"message": "Course not exist"}
    course = CourseModel(
        id=course_id,
        name=course_schema.name,
        description=course_schema.description,
        price=course_schema.price,
        updated_at=datetime.datetime.now(),
    )
    return course_repository.update(course)


def delete_course(user_id: int, course_id: int) -> dict:
    user_permission = user.admin_or_mentor_permission_check(user_id)
    if user_permission:
        return user_permission
    if not course_repository.get_by_id(course_id):
        return {"message": "Course not exist"}
    return course_repository.delete(course_id)
