from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.postgres import engine
from db.models import Role, User


def get_all_users() -> list[User]:
    with Session(bind=engine) as db:
        return db.query(User).all()


def get_user_by_username(username: str) -> User | None:
    with Session(bind=engine) as db:
        return db.query(User).filter(User.username == username).first()


def get_user_by_username_and_password(username: str, password: str) -> User | None:
    with Session(bind=engine) as db:
        return db.query(User).filter(User.username == username, User.password == password).first()


def create_user(user: User) -> int:
    with Session(bind=engine) as db:
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id
        except SQLAlchemyError:
            db.rollback()
            raise


def get_user_by_id(user_id: int) -> User | None:
    with Session(bind=engine) as db:
        return db.query(User).filter(User.id == user_id).first()


def get_user_role(user_id: int) -> str | None:
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        role = db.query(Role).filter(Role.id == user.role_id).first()
        role_name = (role.name if role else "").lower()
        if "админ" in role_name or "admin" in role_name:
            return "admin"
        if "преп" in role_name or "mentor" in role_name or "teacher" in role_name:
            return "mentor"
        if "студ" in role_name or "student" in role_name:
            return "student"
        return role.name if role else None
