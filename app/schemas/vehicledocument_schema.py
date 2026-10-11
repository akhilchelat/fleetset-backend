from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.vehicledocument import VehicleDocumentType


ALLOWED_DOCUMENT_TYPES = {
    VehicleDocumentType.REGISTRATION_CERTIFICATE,
    VehicleDocumentType.INSURANCE,
    VehicleDocumentType.FITNESS_CERTIFICATE,
    VehicleDocumentType.POLLUTION_CERTIFICATE,
    VehicleDocumentType.NATIONAL_PERMIT,
    VehicleDocumentType.STATE_PERMIT,
    VehicleDocumentType.ROAD_TAX,
    VehicleDocumentType.OTHER,
}


class VehicleDocumentCreate(BaseModel):
    vehicle_id: UUID

    document_type: str = VehicleDocumentType.OTHER

    document_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    issue_date: date

    expiry_date: date

    file_url: str = Field(
        ...,
        min_length=1,
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str):
        if value not in ALLOWED_DOCUMENT_TYPES:
            raise ValueError(
                "Invalid document type. "
                f"Allowed values: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}"
            )

        return value

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, value: date, info):
        issue_date = info.data.get("issue_date")

        if issue_date is not None and value < issue_date:
            raise ValueError(
                "Expiry date cannot be earlier than issue date"
            )

        return value


class VehicleDocumentUpdate(BaseModel):
    document_type: str | None = None

    document_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    issue_date: date | None = None

    expiry_date: date | None = None

    file_url: str | None = Field(
        default=None,
        min_length=1,
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str | None):
        if value is None:
            return value

        if value not in ALLOWED_DOCUMENT_TYPES:
            raise ValueError(
                "Invalid document type. "
                f"Allowed values: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}"
            )

        return value


class VehicleDocumentRenew(BaseModel):
    document_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    issue_date: date

    expiry_date: date

    file_url: str = Field(
        ...,
        min_length=1,
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, value: date, info):
        issue_date = info.data.get("issue_date")

        if issue_date is not None and value < issue_date:
            raise ValueError(
                "Expiry date cannot be earlier than issue date"
            )

        return value


class VehicleDocumentResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID
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
        min_length=1,
    )