from sqlalchemy.orm import configure_mappers

# Import all models so SQLAlchemy knows about them
from app.models.company import Company
from app.models.driver import Driver
from app.models.drivervehicleassignment import DriverVehicleAssignment
from app.models.fuel_log import FuelLog
from app.models.maintenance_record import MaintenanceRecord
from app.models.notification import Notification
from app.models.role import Role
from app.models.trip import Trip
from app.models.tripupdate import TripUpdate
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicledocument import VehicleDocument
from app.models.vehicletelemetry import VehicleTelemetry

# Configure all SQLAlchemy mappers
configure_mappers()

print("========================================")
print("SQLAlchemy Relationship Check")
print("========================================")
print("SUCCESS: All model relationships are valid.")
print("========================================")