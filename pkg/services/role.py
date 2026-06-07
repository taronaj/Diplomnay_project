from pkg.repositories import role as role_repository
from schemas.role import RoleSchema


def get_all_roles():
    return role_repository.get_all_roles()


def create_role(role: RoleSchema):
    return role_repository.create_role(role.name)


def assign_role_to_user(user_id: int, role_id: int):
    return role_repository.assign_role_to_user(user_id, role_id)


def soft_delete_role(role_id: int):
    role = role_repository.get_role_by_id(role_id)

    if not role:
        return {"error": "Role not found"}, 404

    if role.name == "Admin":
        return {"error": "This role cannot be deleted"}, 403

    result = role_repository.soft_delete_role(role_id)

    if result is None:
        return {"error": "Error deleting role"}, 500

    if result == "Forbidden":
        return {"error": "This role cannot be deleted"}, 403

    return {"message": "Role successfully soft deleted", "role_id": result}, 200
