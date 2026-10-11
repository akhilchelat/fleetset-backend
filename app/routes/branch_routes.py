from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models.user import User

from app.schemas.branch_schema import (
    BranchBulkAction,
    BranchBulkActionResponse,
    BranchCreate,
    BranchResponse,
    BranchUpdate,
)

from app.security.authorization import (
    get_current_user,
    require_roles,
)

from app.services.branch_service import (
    activate_branch,
    bulk_activate_branches,
    bulk_deactivate_branches,
    create_branch,
    deactivate_branch,
    find_branch_by_id,
    get_all_active_branches,
    get_company_branches,
    update_branch,
)


router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
)


@router.post(
    "/",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_branch_route(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = create_branch(
        db=db,
        current_user=current_user,
        company_id=branch.company_id,
        name=branch.name,
        email=branch.email,
        phone=branch.phone,
        address=branch.address,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/all",
    response_model=list[BranchResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_active_branches_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_all_active_branches(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/company/{company_id}",
    response_model=list[BranchResponse],
    status_code=status.HTTP_200_OK,
)
def get_company_branches_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_company_branches(
        db=db,
        current_user=current_user,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{branch_id}",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
)
def get_branch_by_id_route(
    branch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_branch_by_id(
        db=db,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{branch_id}",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
)
def update_branch_route(
    branch_id: UUID,
    branch: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = update_branch(
        db=db,
        current_user=current_user,
        branch_id=branch_id,
        company_id=branch.company_id,
        name=branch.name,
        email=branch.email,
        phone=branch.phone,
        address=branch.address,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{branch_id}/activate",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
)
def activate_branch_route(
    branch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = activate_branch(
        db=db,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{branch_id}/deactivate",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_branch_route(
    branch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = deactivate_branch(
        db=db,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/activate",
    response_model=BranchBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_activate_branches_route(
    request: BranchBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = bulk_activate_branches(
        db=db,
        current_user=current_user,
        branch_ids=request.branch_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/deactivate",
    response_model=BranchBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_deactivate_branches_route(
    request: BranchBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    result = bulk_deactivate_branches(
        db=db,
        current_user=current_user,
        branch_ids=request.branch_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]