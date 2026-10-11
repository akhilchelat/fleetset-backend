from uuid import UUID

from sqlalchemy.orm import Session

from app.models.branch import Branch


def get_branch_by_id_query(db: Session, branch_id: UUID):
    return (
        db.query(Branch)
        .filter(
            Branch.id == branch_id,
            Branch.is_active.is_(True),
        )
        .first()
    )


def get_branch_by_id_admin_query(db: Session, branch_id: UUID):
    return (
        db.query(Branch)
        .filter(Branch.id == branch_id)
        .first()
    )


def get_branch_by_company_query(
    db: Session,
    branch_id: UUID,
    company_id: UUID,
):
    return (
        db.query(Branch)
        .filter(
            Branch.id == branch_id,
            Branch.company_id == company_id,
            Branch.is_active.is_(True),
        )
        .first()
    )


def get_all_active_branches_query(
    db: Session,
    company_id: UUID | None = None,
):
    query = db.query(Branch).filter(
        Branch.is_active.is_(True)
    )

    if company_id is not None:
        query = query.filter(
            Branch.company_id == company_id
        )

    return query.all()