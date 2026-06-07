from fastapi import APIRouter, Depends
from schemas.course_members import CourseMembers
from pkg.services import course_members as course_members_service
from pkg.controllers.middlewares import get_current_user
from utils.auth import TokenPayload

router = APIRouter(prefix='/course-members', tags=['course_members'])


@router.get("/{course_id}", summary="Get all course members")
def course_members(course_id: int):
    members = course_members_service.course_members(course_id)
    return {'members': members}


@router.post("/{course_id}/{member_id}", summary="Add member to course")
def add_course_member(course_id: int, member_id: int, payload: TokenPayload = Depends(get_current_user)):
    user_id = payload.id
    return course_members_service.add_course_member(course_id, member_id, user_id)


@router.delete("/{course_id}/{member_id}", summary="Delete member from course")
def delete_course_member(course_id: int, member_id: int , payload: TokenPayload = Depends(get_current_user)):
    user_id = payload.id
    return course_members_service.delete_course_member(course_id, member_id, user_id)



