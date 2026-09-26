from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from app.models.role import Role
from app.reusable_functions.role_reusable import (get_role_by_name_query,
                                                  get_role_by_id_query,
                                                  get_all_active_roles_query,
                                                  get_all_roles_admin_query,
                                                  get_role_by_id_admin_query,
                                                  get_roles_by_ids_query)


def find_role_by_id(
    db: Session,
    role_id: UUID
):

    role = get_role_by_id_query(
        db,
        role_id
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ROLE_FOUND",
        "message": "Role found successfully",
        "data": role
    }


def find_role_by_name(
    db: Session,
    role_name: str
):

    role = get_role_by_name_query(
        db,
        role_name
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ROLE_FOUND",
        "message": "Role found successfully",
        "data": role
    }


def get_all_roles(
    db: Session
):

    roles = get_all_active_roles_query(
        db
    )

    if not roles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_ROLES_FOUND",
            "message": "No roles found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ROLES_FOUND",
        "message": "Roles retrieved successfully",
        "data": roles
    }


def get_all_roles_admin(
    db: Session
):

    roles = get_all_roles_admin_query(
        db
    )

    if not roles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_ROLES_FOUND",
            "message": "No roles found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ROLES_FOUND",
        "message": "Roles retrieved successfully",
        "data": roles
    }


def activate_role(
    db: Session,
    role_id: UUID
):

    role = get_role_by_id_admin_query(
        db,
        role_id
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    if role.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ROLE_ALREADY_ACTIVE",
            "message": "Role already active",
            "data": None
        }

    role.is_active = True

    try:
        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ROLE_ACTIVATED",
            "message": "Role activated successfully",
            "data": role
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
        

def bulk_activate_roles(
    db: Session,
    role_ids: list[UUID]
):

    roles = get_roles_by_ids_query(
        db,
        role_ids
    )

    if not roles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_ROLES_FOUND",
            "message": "No roles found",
            "data": None
        }

    already_active_roles = []
    activated_roles = []

    for role in roles:

        if role.is_active:

            already_active_roles.append(
                {
                    "id": str(role.id),
                    "name": role.name
                }
            )

            continue

        role.is_active = True

        activated_roles.append(
            {
                "id": str(role.id),
                "name": role.name
            }
        )

    if len(already_active_roles) == len(roles):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_ROLES_ALREADY_ACTIVE",
            "message": "All roles are already active",
            "data": {
                "roles": already_active_roles
            }
        }

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ROLES_ACTIVATED",
            "message": "Roles activated successfully",
            "data": {
                "activated_roles": activated_roles,
                "already_active_roles": already_active_roles
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def deactivate_role(
    db: Session,
    role_id: UUID
):

    role = get_role_by_id_admin_query(
        db,
        role_id
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    if not role.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ROLE_ALREADY_INACTIVE",
            "message": "Role already inactive",
            "data": None
        }

    role.is_active = False

    try:
        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ROLE_DEACTIVATED",
            "message": "Role deactivated successfully",
            "data": role
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
        

def bulk_deactivate_roles(
    db: Session,
    role_ids: list[UUID]
):

    roles = get_roles_by_ids_query(
        db,
        role_ids
    )

    if not roles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_ROLES_FOUND",
            "message": "No roles found",
            "data": None
        }

    already_inactive_roles = []
    deactivated_roles = []

    for role in roles:

        if not role.is_active:

            already_inactive_roles.append(
                {
                    "id": str(role.id),
                    "name": role.name
                }
            )

            continue

        role.is_active = False

        deactivated_roles.append(
            {
                "id": str(role.id),
                "name": role.name
            }
        )

    if len(already_inactive_roles) == len(roles):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_ROLES_ALREADY_INACTIVE",
            "message": "All roles are already inactive",
            "data": {
                "roles": already_inactive_roles
            }
        }

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ROLES_DEACTIVATED",
            "message": "Roles deactivated successfully",
            "data": {
                "deactivated_roles": deactivated_roles,
                "already_inactive_roles": already_inactive_roles
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }


def find_role_by_id_admin(
    db: Session,
    role_id: UUID
):

    role = get_role_by_id_admin_query(
        db,
        role_id
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ROLE_FOUND",
        "message": "Role found successfully",
        "data": role
    }    