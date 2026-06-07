import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.postgres import engine
from db.models import Comment, Lesson, User
from pkg.controllers.middlewares import get_current_user
from schemas.comments import CreateComment, CommentUpdate

router = APIRouter(tags=["Comments"])


def _comment_to_dict(comment: Comment):
    return {
        "id": comment.id,
        "lesson_id": comment.lesson_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@router.post("/comments/", summary="Create a new comment")
async def create_comment(comment: CreateComment, current_user=Depends(get_current_user)):
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        lesson = db.query(Lesson).filter(Lesson.id == comment.lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        new_comment = Comment(
            lesson_id=comment.lesson_id,
            user_id=user.id,
            content=comment.content,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        return _comment_to_dict(new_comment)


@router.get("/comments/{lesson_id}")
async def get_comments(lesson_id: int, current_user=Depends(get_current_user)):
    with Session(bind=engine) as db:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        comments = (
            db.query(Comment)
            .filter(Comment.lesson_id == lesson_id)
            .order_by(Comment.created_at.asc())
            .all()
        )
        return [_comment_to_dict(comment) for comment in comments]


@router.put("/comments/{comment_id}")
async def update_comment(comment_id: int, comment: CommentUpdate, current_user=Depends(get_current_user)):
    with Session(bind=engine) as db:
        comment_to_update = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.user_id == current_user.id)
            .first()
        )
        if not comment_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

        comment_to_update.content = comment.content
        comment_to_update.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(comment_to_update)
        return _comment_to_dict(comment_to_update)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, current_user=Depends(get_current_user)):
    with Session(bind=engine) as db:
        comment_to_delete = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.user_id == current_user.id)
            .first()
        )
        if not comment_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

        db.delete(comment_to_delete)
        db.commit()
        return None
