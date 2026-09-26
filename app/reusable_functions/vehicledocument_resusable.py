from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle
from app.models.vehicledocument import VehicleDocument, VehicleDocumentType


def get_vehicle_document_by_id_query(db: Session, document_id: UUID) -> VehicleDocument | None:

    return (db.query(VehicleDocument).filter(VehicleDocument.id == document_id,
                                              VehicleDocument.is_active.is_(True)).first())


def get_vehicle_document_by_id_admin_query(db: Session, document_id: UUID) -> VehicleDocument | None:

    return (db.query(VehicleDocument).filter(VehicleDocument.id == document_id).first())


def get_vehicle_documents_by_ids_query(db: Session, company_id: UUID, document_ids: list[UUID]) -> list[VehicleDocument]:

    return (db.query(VehicleDocument).join(Vehicle).filter(Vehicle.company_id == company_id,
                                                            VehicleDocument.id.in_(document_ids),
                                                            VehicleDocument.is_active.is_(True)).all())


def get_all_active_vehicle_documents_query(db: Session, company_id: UUID) -> list[VehicleDocument]:

    return (db.query(VehicleDocument).join(Vehicle).filter(Vehicle.company_id == company_id,
                                                           VehicleDocument.is_active.is_(True))
                                                           .order_by(VehicleDocument.expiry_date.asc()).all())


def get_all_inactive_vehicle_documents_query(db: Session, company_id: UUID) -> list[VehicleDocument]:

    return (db.query(VehicleDocument).join(Vehicle).filter(Vehicle.company_id == company_id,
                                                            VehicleDocument.is_active.is_(False))
                                                            .order_by(VehicleDocument.expiry_date.asc()).all())


def get_vehicle_document_by_type_query(db: Session, vehicle_id: UUID, document_type: str) -> VehicleDocument | None:

    return (db.query(VehicleDocument).filter(VehicleDocument.vehicle_id == vehicle_id, 
                                             VehicleDocument.document_type == document_type,
                                             VehicleDocument.is_active.is_(True)).first())


def create_vehicle_document_query(db: Session, document: VehicleDocument) -> VehicleDocument:

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def update_vehicle_document_query(db: Session, document: VehicleDocument) -> VehicleDocument:

    db.commit()
    db.refresh(document)

    return document

def get_active_document_by_type_query(db: Session, vehicle_id: UUID, document_type: VehicleDocumentType) -> VehicleDocument | None:

    return (db.query(VehicleDocument).filter(VehicleDocument.vehicle_id == vehicle_id, 
                                             VehicleDocument.document_type == document_type, 
                                             VehicleDocument.is_active.is_(True)).first())


def deactivate_vehicle_document_query(db: Session, document: VehicleDocument) -> VehicleDocument:

    document.is_active = False

    db.commit()
    db.refresh(document)

    return document


def get_company_documents_by_type_query(db: Session, company_id: UUID, document_type: VehicleDocumentType,) -> list[VehicleDocument]:

    return (db.query(VehicleDocument).filter(VehicleDocument.company_id == company_id,
                                             VehicleDocument.document_type == document_type,
                                             VehicleDocument.is_active.is_(True),)
                                             .order_by(VehicleDocument.expiry_date.asc()).all())


def renew_vehicle_document_query(
    db: Session,
    old_document: VehicleDocument,
    new_document: VehicleDocument,
) -> VehicleDocument:

    try:
        # Deactivate old document
        old_document.is_active = False

        # Add renewed document
        db.add(new_document)

        # Commit both operations together
        db.commit()

        # Refresh the newly created document
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
) -> list[VehicleDocument]:

    return (
        db.query(VehicleDocument)
        .filter(
            VehicleDocument.company_id == company_id,
            VehicleDocument.is_active.is_(True),
            VehicleDocument.expiry_date >= start_date,
            VehicleDocument.expiry_date <= end_date,
        )
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )


def get_expired_vehicle_documents_query(
    db: Session,
    company_id: UUID,
    today: date,
) -> list[VehicleDocument]:

    return (
        db.query(VehicleDocument)
        .filter(
            VehicleDocument.company_id == company_id,
            VehicleDocument.is_active.is_(True),
            VehicleDocument.expiry_date < today,
        )
        .order_by(VehicleDocument.expiry_date.asc())
        .all()
    )