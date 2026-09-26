from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.vehicledocument import VehicleDocumentType


class VehicleDocumentCreate(BaseModel):
    vehicle_id: UUID
    uploaded_by: UUID
    document_type: str = VehicleDocumentType.OTHER
    document_number: str = Field(..., min_length=1, max_length=100)
    issue_date: date
    expiry_date: date
    file_url: str = Field(..., min_length=1)
    remarks: str | None = None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str):
        allowed_types = {
            VehicleDocumentType.REGISTRATION_CERTIFICATE,
            VehicleDocumentType.INSURANCE,
            VehicleDocumentType.FITNESS_CERTIFICATE,
            VehicleDocumentType.POLLUTION_CERTIFICATE,
            VehicleDocumentType.NATIONAL_PERMIT,
            VehicleDocumentType.STATE_PERMIT,
            VehicleDocumentType.ROAD_TAX,
            VehicleDocumentType.OTHER,
        }

        if value not in allowed_types:
            raise ValueError(
                "Invalid document type. "
                f"Allowed values: {', '.join(sorted(allowed_types))}"
            )

        return value


class VehicleDocumentUpdate(BaseModel):
    document_type: str | None = None
    document_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    issue_date: date | None = None
    expiry_date: date | None = None
    file_url: str | None = Field(
        default=None,
        min_length=1
    )
    remarks: str | None = None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str | None):
        if value is None:
            return value

        allowed_types = {
            VehicleDocumentType.REGISTRATION_CERTIFICATE,
            VehicleDocumentType.INSURANCE,
            VehicleDocumentType.FITNESS_CERTIFICATE,
            VehicleDocumentType.POLLUTION_CERTIFICATE,
            VehicleDocumentType.NATIONAL_PERMIT,
            VehicleDocumentType.STATE_PERMIT,
            VehicleDocumentType.ROAD_TAX,
            VehicleDocumentType.OTHER,
        }

        if value not in allowed_types:
            raise ValueError(
                "Invalid document type. "
                f"Allowed values: {', '.join(sorted(allowed_types))}"
            )

        return value


class VehicleDocumentRenew(BaseModel):
    uploaded_by: UUID
    document_number: str = Field(
        ...,
        min_length=1,
        max_length=100
    )
    issue_date: date
    expiry_date: date
    file_url: str = Field(
        ...,
        min_length=1
    )
    remarks: str | None = None


class VehicleDocumentResponse(BaseModel):
    id: UUID
    company_id: UUID
    vehicle_id: UUID
    uploaded_by: UUID
    document_type: str
    document_number: str
    issue_date: date | None = None
    expiry_date: date | None = None
    file_url: str | None = None
    remarks: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentBulkRequest(BaseModel):
    document_ids: list[UUID] = Field(
        ...,
        min_length=1
    )

