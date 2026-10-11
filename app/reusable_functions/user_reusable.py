from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email_query(
    db: Session,
    email: str,
):
    return (
        db.query(User)
        .filter(
            User.email == email,
            User.is_active.is_(True),
        )
        .first()
    )


def get_user_by_email_auth_query(
    db: Session,
    email: str,
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_user_by_email_admin_query(
    db: Session,
    email: str,
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_user_by_id_query(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active.is_(True),
        )
        .first()
    )


def get_user_by_id_admin_query(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def get_all_users_query(
    db: Session,
):
    return (
        db.query(User)
        .filter(User.is_active.is_(True))
        .all()
    )


def get_all_users_admin_query(
    db: Session,
):
    return db.query(User).all()


def get_users_by_ids_query(
    db: Session,
    user_ids: list[UUID],
):
    return (
        db.query(User)
        .filter(User.id.in_(user_ids))
        .all()
    )


def get_users_by_company_query(
    db: Session,
    company_id: UUID,
    active_only: bool = True,
):
    query = db.query(User).filter(
        User.company_id == company_id
    )

    if active_only:
        query = query.filter(
            User.is_active.is_(True)
        )

    return query.all()


def get_users_by_branch_query(
    db: Session,
    branch_id: UUID,
    active_only: bool = True,
):
    query = db.query(User).filter(
        User.branch_id == branch_id
    )

    if active_only:
        query = query.filter(
            User.is_active.is_(True)
        )

    return query.all()


def get_user_by_scope_query(
    db: Session,
    user_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(User).filter(
        User.id == user_id
    )

    if active_only:
        query = query.filter(
            User.is_active.is_(True)
        )

    if company_id is not None:
        query = query.filter(
            User.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            User.branch_id == branch_id
        )

    return query.first()