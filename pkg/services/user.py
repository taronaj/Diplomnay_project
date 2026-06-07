import datetime

from logger.logger import logger
from utils.hash import hash_password, verify_password
from pkg.repositories import user as user_repository
from schemas.user import UserSchema
from db.models import User


def get_user_by_username(username: str) -> User | None:
    return user_repository.get_user_by_username(username)


def get_user_by_username_and_password(username: str, password: str) -> User | None:
    user = user_repository.get_user_by_username(username)

    if user is None:
        return None

    if not verify_password(password, user.password):
        logger.error("Invalid password attempt")
        return None

    return user


def create_user(user: UserSchema) -> dict:
    new_user = User()
    new_user.full_name = user.full_name
    new_user.username = user.username
    new_user.password = hash_password(user.password)
    new_user.role_id = 1
    new_user.created_at = datetime.datetime.now()

    return user_repository.create_user(new_user)


def get_all_users() -> list[User]:
    return user_repository.get_all_users()


def admin_or_mentor_permission_check(user_id: int) -> dict | None:
    if user_repository.get_user_role(user_id) not in ["admin", "mentor"]:
        return {"message": "Only admin or mentor has permission"}
    return None
