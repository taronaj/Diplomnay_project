from fastapi import APIRouter, HTTPException, status

from schemas.user import UserSchema, UserSignInSchema
from pkg.services import event as event_service
from pkg.services import user as user_service
from utils.auth import create_access_token

router = APIRouter(tags=["Authentication"])


@router.post("/sign-up", status_code=status.HTTP_201_CREATED, summary="Register user")
def sign_up(user: UserSchema):
    user_from_db = user_service.get_user_by_username(user.username)
    if user_from_db is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")

    user_service.create_user(user)
    return {"message": "User created successfully"}


@router.post("/sign-in", summary="Sign in and receive JWT token")
def sign_in(user: UserSignInSchema):
    user_from_db = user_service.get_user_by_username_and_password(user.username, user.password)
    if user_from_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong login or password")

    event_service.log_event(
        user_id=user_from_db.id,
        event_type="user_sign_in",
        event_description=f"Пользователь {user_from_db.username} вошел в систему",
        related_id=user_from_db.id,
    )

    access_token = create_access_token({"id": user_from_db.id, "role_id": user_from_db.role_id})
    return {"access_token": access_token, "token_type": "bearer"}
