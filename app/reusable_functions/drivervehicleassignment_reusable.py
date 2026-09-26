from uuid import UUID
from sqlalchemy.orm import Session
from app.models.drivervehicleassignment import DriverVehicleAssignment
from app.models.driver import Driver
from app.models.vehicle import Vehicle

def get_assignment_by_id_query(db: Session, assignment_id: UUID) -> DriverVehicleAssignment | None:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.id == assignment_id) .first())


def get_active_assignment_by_driver_id_query(db: Session, driver_id: UUID) -> DriverVehicleAssignment | None:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.driver_id == driver_id, 
                                                     DriverVehicleAssignment.is_active.is_(True)).first())


def get_active_assignment_by_vehicle_id_query(db: Session, vehicle_id: UUID) -> DriverVehicleAssignment | None:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.vehicle_id == vehicle_id,
                                                     DriverVehicleAssignment.is_active.is_(True)).first())


def get_driver_assignments_query(db: Session, driver_id: UUID) -> list[DriverVehicleAssignment]:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.driver_id == driver_id)
            .order_by(DriverVehicleAssignment.assigned_at.desc()).all())


def get_vehicle_assignments_query(db: Session, vehicle_id: UUID) -> list[DriverVehicleAssignment]:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.vehicle_id == vehicle_id)
            .order_by(DriverVehicleAssignment.assigned_at.desc()).all())


def get_company_assignments_query(db: Session, company_id: UUID) -> list[DriverVehicleAssignment]:
    
    return (db.query(DriverVehicleAssignment).filter(DriverVehicleAssignment.company_id == company_id)
            .order_by(DriverVehicleAssignment.assigned_at.desc()).all())


def create_assignment_query(db: Session, assignment: DriverVehicleAssignment) -> DriverVehicleAssignment:
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return assignment


def update_assignment_query(db: Session, assignment: DriverVehicleAssignment) -> DriverVehicleAssignment:
    
    db.commit()
    db.refresh(assignment)
    
    return assignment


def deactivate_assignment_query(db: Session,assignment: DriverVehicleAssignment) -> DriverVehicleAssignment:
    
    assignment.is_active = False
    db.commit()
    db.refresh(assignment)
    
    return assignment