import json

from fastapi import APIRouter, status, Depends, HTTPException
from starlette.responses import Response

from pkg.controllers.middlewares import get_current_user, require_roles
from pkg.services import role as role_service
from schemas.role import RoleSchema

router = APIRouter()


@router.get("/")
def ping_pong():
    return {"ping": "pong"}


@router.get("/roles", summary="Get all roles", tags=["roles"])
def get_all_roles(payload=Depends(require_roles("Администратор"))):
    roles = role_service.get_all_roles()
    return [{"id": role.id, "name": role.name} for role in roles]  # Convert to dictionary manually


@router.post("/roles", summary="Create a new role", tags=["roles"])
def create_role(role: RoleSchema, payload=Depends(require_roles("Администратор"))):
    role_id = role_service.create_role(role)
    return Response(json.dumps({'message': 'Successfully created role', 'role_id': role_id}),
                    status_code=status.HTTP_201_CREATED,
                    media_type='application/json')


@router.post("/roles/assign", summary="Assign role to user", tags=["roles"])
def assign_role(user_id: int, role_id: int, payload=Depends(require_roles("Администратор"))):
    user = role_service.assign_role_to_user(user_id, role_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return Response(json.dumps({'message': 'Role assigned successfully'}), status_code=status.HTTP_200_OK)


@router.delete("/roles/{role_id}", summary="Soft delete a role", tags=["roles"])
def soft_delete_role(role_id: int, payload=Depends(require_roles("Администратор"))):
    response, status_code = role_service.soft_delete_role(role_id)

    return Response(json.dumps(response), status_code=status_code, media_type='application/json')
