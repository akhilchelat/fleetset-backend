from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.company_routes import router as company_router
from app.routes.driver_routes import router as driver_router
from app.routes.vehicle_routes import router as vehicle_router
from app.routes.trip_routes import router as trip_router
from app.routes.user_routes import router as user_router
from app.routes.maintenance_routes import router as maintenance_router
from app.routes.drivervehicleassignment_route import (
    router as drivervehicleassignment_router
)
from app.routes.role_routes import router as role_router
from app.routes.vehicledocument_routes import router as vehicledocument_router
from app.routes.fuel_log_route import router as fuel_log_router
from app.routes.auth_route import router as auth_router
from app.routes.report_routes import router as report_router


app = FastAPI(
    title="FleetSet API",
    version="1.0.0",
)


# =========================
# CORS CONFIGURATION
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ROUTES
# =========================

app.include_router(company_router)
app.include_router(driver_router)
app.include_router(vehicle_router)
app.include_router(trip_router)
app.include_router(user_router)
app.include_router(maintenance_router)
app.include_router(drivervehicleassignment_router)
app.include_router(role_router)
app.include_router(vehicledocument_router)
app.include_router(fuel_log_router)
app.include_router(auth_router)
app.include_router(report_router)