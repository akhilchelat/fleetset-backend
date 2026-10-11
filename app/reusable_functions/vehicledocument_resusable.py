from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.vehicledocument import VehicleDocument


def get_vehicle_document_by_id_query(
    db: Session,
    document_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> VehicleDocument | None:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.id == document_id,
        VehicleDocument.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            VehicleDocument.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return query.first()


def get_vehicle_document_by_id_admin_query(
    db: Session,
    document_id: UUID,
) -> VehicleDocument | None:
    return (
        db.query(VehicleDocument)
        .filter(VehicleDocument.id == document_id)
        .first()
    )


def get_vehicle_documents_by_ids_query(
    db: Session,
    company_id: UUID,
    document_ids: list[UUID],
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.id.in_(document_ids),
        VehicleDocument.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return query.all()


def get_all_active_vehicle_documents_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_all_inactive_vehicle_documents_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.is_active.is_(False),
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_vehicle_documents_query(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.vehicle_id == vehicle_id,
    )

    if company_id is not None:
        query = query.filter(
            VehicleDocument.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    if active_only:
        query = query.filter(
            VehicleDocument.is_active.is_(True)
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_vehicle_document_by_type_query(
    db: Session,
    vehicle_id: UUID,
    document_type: str,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> VehicleDocument | None:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.vehicle_id == vehicle_id,
        VehicleDocument.document_type == document_type,
        VehicleDocument.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            VehicleDocument.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return query.first()


def get_active_document_by_type_query(
    db: Session,
    vehicle_id: UUID,
    document_type: str,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> VehicleDocument | None:
    return get_vehicle_document_by_type_query(
        db=db,
        vehicle_id=vehicle_id,
        document_type=document_type,
        company_id=company_id,
        branch_id=branch_id,
    )


def get_company_documents_by_type_query(
    db: Session,
    company_id: UUID,
    document_type: str,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.document_type == document_type,
        VehicleDocument.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def create_vehicle_document_query(
    db: Session,
    document: VehicleDocument,
) -> VehicleDocument:
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def update_vehicle_document_query(
    db: Session,
    document: VehicleDocument,
) -> VehicleDocument:
    db.commit()
    db.refresh(document)

    return document


def deactivate_vehicle_document_query(
    db: Session,
    document: VehicleDocument,
) -> VehicleDocument:
    document.is_active = False

    db.commit()
    db.refresh(document)

    return document


def renew_vehicle_document_query(
    db: Session,
    old_document: VehicleDocument,
    new_document: VehicleDocument,
) -> VehicleDocument:
    try:
        old_document.is_active = False

        db.add(new_document)

        db.commit()
        db.refresh(new_document)

        return new_document

    except Exception:
        db.rollback()
        raise


def get_expiring_vehicle_documents_query(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.is_active.is_(True),
        VehicleDocument.expiry_date.isnot(None),
        VehicleDocument.expiry_date >= start_date,
        VehicleDocument.expiry_date <= end_date,
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_expired_vehicle_documents_query(
    db: Session,
    company_id: UUID,
    today: date,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.is_active.is_(True),
        VehicleDocument.expiry_date.isnot(None),
        VehicleDocument.expiry_date < today,
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_documents_expiring_by_date_query(
    db: Session,
    company_id: UUID,
    target_date: date,
    branch_id: UUID | None = None,
) -> list[VehicleDocument]:
    query = db.query(VehicleDocument).filter(
        VehicleDocument.company_id == company_id,
        VehicleDocument.is_active.is_(True),
        VehicleDocument.expiry_date == target_date,
    )

    if branch_id is not None:
        query = query.filter(
            VehicleDocument.branch_id == branch_id
        )

    return (
        query
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )