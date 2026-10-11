from uuid import UUID

from sqlalchemy.orm import Session

from app.models.role import Role


def get_role_by_name_query(
    db: Session,
    role_name: str,
):
    return (
        db.query(Role)
        .filter(
            Role.name == role_name,
            Role.is_active.is_(True),
        )
        .first()
    )


def get_role_by_id_query(
    db: Session,
    role_id: UUID,
):
    return (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.is_active.is_(True),
        )
        .first()
    )


def get_role_by_id_admin_query(
    db: Session,
    role_id: UUID,
):
    return (
        db.query(Role)
        .filter(Role.id == role_id)
        .first()
    )


def get_all_active_roles_query(
    db: Session,
):
    return (
        db.query(Role)
        .filter(Role.is_active.is_(True))
        .all()
    )


def get_all_roles_admin_query(
    db: Session,
):
    return db.query(Role).all()


def get_roles_by_ids_query(
    db: Session,
    role_ids: list[UUID],
):
    return (
        db.query(Role)
        .filter(Role.id.in_(role_ids))
        .all()
    )