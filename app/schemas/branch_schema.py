from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BranchCreate(BaseModel):
    company_id: UUID

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    address: str | None = None


class BranchUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    address: str | None = None


class BranchResponse(BaseModel):
    id: UUID
    company_id: UUID

    name: str
    email: EmailStr | None
    phone: str | None
    address: str | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class BranchBulkAction(BaseModel):
    branch_ids: list[UUID] = Field(
        ...,
        min_length=1,
    )


class BranchBulkActionResponse(BaseModel):
    activated_branches: list[dict] | None = None
    already_active_branches: list[dict] | None = None

    deactivated_branches: list[dict] | None = None
    already_inactive_branches: list[dict] | None = None

    inaccessible_branches: list[dict] | None = None