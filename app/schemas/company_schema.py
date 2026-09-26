from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class CompanyBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str
    gst_number: str


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    gst_number: str | None = None


class CompanyResponse(CompanyBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CompanyBulkAction(BaseModel):
    company_ids: list[UUID]


class CompanyBulkActionItem(BaseModel):
    id: UUID
    name: str


class CompanyBulkActionResponse(BaseModel):
    activated_companies: list[CompanyBulkActionItem] = []
    deactivated_companies: list[CompanyBulkActionItem] = []
    already_active_companies: list[CompanyBulkActionItem] = []
    already_inactive_companies: list[CompanyBulkActionItem] = []