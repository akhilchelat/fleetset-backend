
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.user import User

from app.reusable_functions.branch_reusable import (
    get_all_active_branches_query,
    get_branch_by_company_query,
    get_branch_by_id_admin_query,
    get_branch_by_id_query,
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)


GLOBAL_ADMIN = "GLOBAL_ADMIN"
SUPER_ADMIN = "SUPER_ADMIN"
BRANCH_ADMIN = "BRANCH_ADMIN"
DRIVER = "DRIVER"


def _get_role_name(
    current_user: User,
):
    if not current_user.role:
        return None

    return current_user.role.name


def _can_access_company(
    current_user: User,
    company_id: UUID,
):
    role_name = _get_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        return True

    return current_user.company_id == company_id


def _can_access_branch(
    current_user: User,
    branch: Branch,
):
    role_name = _get_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        return True

    if current_user.company_id != branch.company_id:
        return False

    if role_name == SUPER_ADMIN:
        return True

    if role_name in {
        BRANCH_ADMIN,
        DRIVER,
    }:
        return current_user.branch_id == branch.id

    return False


def _can_manage_branch(
    current_user: User,
    branch: Branch,
):
    role_name = _get_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        return True

    if role_name == SUPER_ADMIN:
        return current_user.company_id == branch.company_id

    return False


def create_branch(
    db: Session,
    current_user: User,
    company_id: UUID,
    name: str,
    email: str | None,
    phone: str | None,
    address: str | None,
):
    role_name = _get_role_name(current_user)

    if role_name not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_CREATION_FORBIDDEN",
            "message": "You do not have permission to create branches",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You can only create branches in your own company",
            "data": None,
        }

    company = get_company_by_id_query(
        db,
        company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    existing_branch = (
        db.query(Branch)
        .filter(
            Branch.company_id == company_id,
            Branch.name == name,
        )
        .first()
    )

    if existing_branch:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_ALREADY_EXISTS",
            "message": "A branch with this name already exists in this company",
            "data": None,
        }

    new_branch = Branch(
        company_id=company_id,
        name=name,
        email=email,
        phone=phone,
        address=address,
    )

    db.add(new_branch)

    try:
        db.commit()
        db.refresh(new_branch)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "BRANCH_CREATED",
            "message": "Branch created successfully",
            "data": new_branch,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_CREATION_CONFLICT",
            "message": "Branch could not be created because of a data conflict",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def find_branch_by_id(
    db: Session,
    current_user: User,
    branch_id: UUID,
):
    branch = get_branch_by_id_admin_query(
        db,
        branch_id,
    )

    if not branch:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not branch.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not _can_access_branch(
        current_user,
        branch,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "You do not have permission to access this branch",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "BRANCH_FOUND",
        "message": "Branch found successfully",
        "data": branch,
    }


def get_all_active_branches(
    db: Session,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        branches = get_all_active_branches_query(db)

    elif role_name == SUPER_ADMIN:
        if current_user.company_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_REQUIRED",
                "message": "Super admin must belong to a company",
                "data": None,
            }

        branches = get_all_active_branches_query(
            db,
            current_user.company_id,
        )

    elif role_name in {
        BRANCH_ADMIN,
        DRIVER,
    }:
        if current_user.branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "BRANCH_NOT_FOUND",
                "message": "User branch not found",
                "data": None,
            }

        branch = get_branch_by_id_query(
            db,
            current_user.branch_id,
        )

        branches = [branch] if branch else []

    else:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "You do not have permission to access branches",
            "data": None,
        }

    if not branches:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_BRANCHES_FOUND",
            "message": "No branches found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "BRANCHES_FOUND",
        "message": "Branches retrieved successfully",
        "data": branches,
    }


def get_company_branches(
    db: Session,
    current_user: User,
    company_id: UUID,
):
    role_name = _get_role_name(current_user)

    if not _can_access_company(
        current_user,
        company_id,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You can only access branches in your own company",
            "data": None,
        }

    if role_name in {
        BRANCH_ADMIN,
        DRIVER,
    }:
        if current_user.branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "BRANCH_NOT_FOUND",
                "message": "User branch not found",
                "data": None,
            }

        branch = get_branch_by_company_query(
            db,
            current_user.branch_id,
            company_id,
        )

        if not branch:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "BRANCH_NOT_FOUND",
                "message": "User branch not found",
                "data": None,
            }

        branches = [branch]

    else:
        branches = get_all_active_branches_query(
            db,
            company_id,
        )

    if not branches:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_BRANCHES_FOUND",
            "message": "No branches found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "BRANCHES_FOUND",
        "message": "Company branches retrieved successfully",
        "data": branches,
    }


def update_branch(
    db: Session,
    current_user: User,
    branch_id: UUID,
    company_id: UUID | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
):
    branch = get_branch_by_id_admin_query(
        db,
        branch_id,
    )

    if not branch:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not branch.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not _can_manage_branch(
        current_user,
        branch,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update this branch",
            "data": None,
        }

    if company_id is not None and company_id != branch.company_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "COMPANY_CHANGE_FORBIDDEN",
            "message": "A branch cannot be moved to another company",
            "data": None,
        }

    company = get_company_by_id_query(
        db,
        branch.company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    if name is not None:
        existing_branch = (
            db.query(Branch)
            .filter(
                Branch.company_id == branch.company_id,
                Branch.name == name,
                Branch.id != branch.id,
            )
            .first()
        )

        if existing_branch:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "BRANCH_ALREADY_EXISTS",
                "message": "A branch with this name already exists in this company",
                "data": None,
            }

        branch.name = name

    if email is not None:
        branch.email = email

    if phone is not None:
        branch.phone = phone

    if address is not None:
        branch.address = address

    try:
        db.commit()
        db.refresh(branch)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BRANCH_UPDATED",
            "message": "Branch updated successfully",
            "data": branch,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_UPDATE_CONFLICT",
            "message": "Branch update conflicts with existing data",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def activate_branch(
    db: Session,
    current_user: User,
    branch_id: UUID,
):
    branch = get_branch_by_id_admin_query(
        db,
        branch_id,
    )

    if not branch:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not _can_manage_branch(
        current_user,
        branch,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACTIVATION_FORBIDDEN",
            "message": "You do not have permission to activate this branch",
            "data": None,
        }

    if branch.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_ALREADY_ACTIVE",
            "message": "Branch already active",
            "data": None,
        }

    branch.is_active = True

    try:
        db.commit()
        db.refresh(branch)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BRANCH_ACTIVATED",
            "message": "Branch activated successfully",
            "data": branch,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_ACTIVATION_CONFLICT",
            "message": "Branch could not be activated because of a data conflict",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def deactivate_branch(
    db: Session,
    current_user: User,
    branch_id: UUID,
):
    branch = get_branch_by_id_admin_query(
        db,
        branch_id,
    )

    if not branch:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not _can_manage_branch(
        current_user,
        branch,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_DEACTIVATION_FORBIDDEN",
            "message": "You do not have permission to deactivate this branch",
            "data": None,
        }

    if not branch.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_ALREADY_INACTIVE",
            "message": "Branch already inactive",
            "data": None,
        }

    branch.is_active = False

    try:
        db.commit()
        db.refresh(branch)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BRANCH_DEACTIVATED",
            "message": "Branch deactivated successfully",
            "data": branch,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BRANCH_DEACTIVATION_CONFLICT",
            "message": "Branch could not be deactivated because of a data conflict",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def bulk_activate_branches(
    db: Session,
    current_user: User,
    branch_ids: list[UUID],
):
    role_name = _get_role_name(current_user)

    if role_name not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BULK_ACTION_FORBIDDEN",
            "message": "You do not have permission to perform bulk branch actions",
            "data": None,
        }

    branches = (
        db.query(Branch)
        .filter(
            Branch.id.in_(branch_ids),
        )
        .all()
    )

    if not branches:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_BRANCHES_FOUND",
            "message": "No branches found",
            "data": None,
        }

    activated_branches = []
    already_active_branches = []
    inaccessible_branches = []

    for branch in branches:
        if not _can_manage_branch(
            current_user,
            branch,
        ):
            inaccessible_branches.append({
                "id": str(branch.id),
                "name": branch.name,
            })
            continue

        if branch.is_active:
            already_active_branches.append({
                "id": str(branch.id),
                "name": branch.name,
            })
            continue

        branch.is_active = True

        activated_branches.append({
            "id": str(branch.id),
            "name": branch.name,
        })

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_BRANCH_ACTIVATION_COMPLETED",
            "message": "Bulk activation completed",
            "data": {
                "activated_branches": activated_branches,
                "already_active_branches": already_active_branches,
                "inaccessible_branches": inaccessible_branches,
            },
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BULK_BRANCH_ACTIVATION_CONFLICT",
            "message": "Bulk branch activation could not be completed",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def bulk_deactivate_branches(
    db: Session,
    current_user: User,
    branch_ids: list[UUID],
):
    role_name = _get_role_name(current_user)

    if role_name not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BULK_ACTION_FORBIDDEN",
            "message": "You do not have permission to perform bulk branch actions",
            "data": None,
        }

    branches = (
        db.query(Branch)
        .filter(
            Branch.id.in_(branch_ids),
        )
        .all()
    )

    if not branches:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_BRANCHES_FOUND",
            "message": "No branches found",
            "data": None,
        }

    deactivated_branches = []
    already_inactive_branches = []
    inaccessible_branches = []

    for branch in branches:
        if not _can_manage_branch(
            current_user,
            branch,
        ):
            inaccessible_branches.append({
                "id": str(branch.id),
                "name": branch.name,
            })
            continue

        if not branch.is_active:
            already_inactive_branches.append({
                "id": str(branch.id),
                "name": branch.name,
            })
            continue

        branch.is_active = False

        deactivated_branches.append({
            "id": str(branch.id),
            "name": branch.name,
        })

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_BRANCH_DEACTIVATION_COMPLETED",
            "message": "Bulk deactivation completed",
            "data": {
                "deactivated_branches": deactivated_branches,
                "already_inactive_branches": already_inactive_branches,
                "inaccessible_branches": inaccessible_branches,
            },
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BULK_BRANCH_DEACTIVATION_CONFLICT",
            "message": "Bulk branch deactivation could not be completed",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }

