from uuid import UUID

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User


def get_company_by_email(db: Session, email: str):
    return (
        db.query(Company)
        .filter(Company.email == email)
        .first()
    )


def get_company_by_id_query(db: Session, company_id: UUID):
    return (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.is_active.is_(True),
        )
        .first()
    )


def get_company_by_email_query(db: Session, email: str):
    return (
        db.query(Company)
        .filter(
            Company.email == email,
            Company.is_active.is_(True),
        )
        .first()
    )


def get_all_active_companies_query(db: Session):
    return (
        db.query(Company)
        .filter(Company.is_active.is_(True))
        .all()
    )


def get_all_companies_query(db: Session):
    return db.query(Company).all()


def get_company_by_id_admin_query(db: Session, company_id: UUID):
    return (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )


def get_companies_by_ids_query(
    db: Session,
    company_ids: list[UUID],
):
    return (
        db.query(Company)
        .filter(Company.id.in_(company_ids))
        .all()
    )


def get_company_for_user_query(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    query = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active.is_(True),
    )

    if current_user.role.name != "GLOBAL_ADMIN":
        query = query.filter(
            Company.id == current_user.company_id
        )

    return query.first()