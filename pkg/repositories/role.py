import datetime

from sqlalchemy.orm import Session

from db.postgres import engine
from db.models import Role, User

critical_role = ["admin"]


def create_role(role_name: str):
    with Session(bind=engine) as db:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role.id


def get_all_roles():
    with Session(bind=engine) as db:
        return db.query(Role).filter(Role.deleted_at == None).all()


def get_role_by_id(role_id: int):
    with Session(bind=engine) as db:
        return db.query(Role).filter(Role.id == role_id).first()


def assign_role_to_user(user_id: int, role_id: int):
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
        if not user:
            return None

        user.role_id = role_id
        user.updated_at = datetime.datetime.now()
        db.commit()
        return user


def soft_delete_role(role_id: int):
    with Session(bind=engine) as db:
        role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
        if not role:
            return None

        if role.name in critical_role:
            return "Forbidden"

        role.deleted_at = datetime.datetime.now()
        db.commit()
        db.refresh(role)
        return role.id
