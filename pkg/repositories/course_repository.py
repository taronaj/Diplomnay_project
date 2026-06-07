import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import Course as CourseModel
from db.postgres import engine


def _course_to_dict(course: CourseModel) -> dict:
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "price": course.price,
    }


def get_all() -> list[dict]:
    with Session(bind=engine) as db:
        courses = (
            db.query(CourseModel)
            .filter(CourseModel.deleted_at.is_(None))
            .order_by(CourseModel.id.asc())
            .all()
        )
        return [_course_to_dict(course) for course in courses]


def get_by_id(course_id: int) -> CourseModel | None:
    with Session(bind=engine) as db:
        return (
            db.query(CourseModel)
            .filter(CourseModel.id == course_id, CourseModel.deleted_at.is_(None))
            .first()
        )


def create(course: CourseModel) -> dict:
    with Session(bind=engine) as db:
        try:
            new_course = CourseModel(
                name=course.name,
                description=course.description,
                price=course.price,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            db.add(new_course)
            db.commit()
            db.refresh(new_course)
            return {"message": f"Course {new_course.name} created successfully"}
        except SQLAlchemyError:
            db.rollback()
            raise


def update(updated_course: CourseModel) -> dict:
    with Session(bind=engine) as db:
        try:
            course = db.query(CourseModel).filter(CourseModel.id == updated_course.id).first()
            if course is None:
                return {"message": "Course not found"}
            course.name = updated_course.name
            course.price = updated_course.price
            course.description = updated_course.description
            course.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(course)
            return {"message": "Course updated successfully"}
        except SQLAlchemyError:
            db.rollback()
            raise


def delete(course_id: int) -> dict:
    with Session(bind=engine) as db:
        try:
            course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
            if course is None:
                return {"message": "Course not found"}
            course.deleted_at = datetime.datetime.now()
            db.commit()
            db.refresh(course)
            return {"message": "Course deleted successfully"}
        except SQLAlchemyError:
            db.rollback()
            raise
