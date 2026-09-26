from sqlalchemy.orm import Session
from app.models.user import User
from uuid import UUID

def get_user_by_email_query(db: Session, email: str):

    return (db.query(User).filter(User.email == email, User.is_active.is_(True)).first())


def get_user_by_id_query(db: Session, user_id: UUID):

    return (db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first())


def get_all_users_query(db: Session):

    return (db.query(User).filter(User.is_active.is_(True)).all())


def get_all_users_admin_query(db: Session):

    return (db.query(User).all())


def get_user_by_id_admin_query(db: Session, user_id: UUID):

    return (db.query(User).filter(User.id == user_id).first())


def get_users_by_ids_query(db: Session, user_ids: list[UUID]):

    return (db.query(User).filter(User.id.in_(user_ids)).all())


