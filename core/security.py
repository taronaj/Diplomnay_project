from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from db.models import User, Role
from utils.auth import verify_token


def get_current_user(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    token = authorization[len("Bearer "):].strip()
    payload = verify_token(token)
    user = db.query(User).filter(User.id == payload.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_role_name(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> str:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.name if role else ""


def require_roles(*allowed_roles: str):
    allowed = {role.lower() for role in allowed_roles}

    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        role_name = (role.name if role else "").lower()
        if role_name not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return user

    return dependency
