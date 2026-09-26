from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field



class UserCreate(BaseModel):
    company_id: UUID
    role_id: UUID

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    last_name: str | None = Field(
        default=None,
        max_length=100
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=8
    )



class UserUpdate(BaseModel):
    company_id: UUID | None = None
    role_id: UUID | None = None

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    last_name: str | None = Field(
        default=None,
        max_length=100
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20
    )


class UserResponse(BaseModel):
    id: UUID

    company_id: UUID
    role_id: UUID

    first_name: str
    last_name: str | None

    email: EmailStr
    phone: str | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class UserBulkAction(BaseModel):
    user_ids: list[UUID] = Field(
        ...,
        min_length=1
    )


class UserBulkActionResponse(BaseModel):
    activated_users: list[dict] | None = None
    already_active_users: list[dict] | None = None

    deactivated_users: list[dict] | None = None
    already_inactive_users: list[dict] | None = None
