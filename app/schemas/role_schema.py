from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RoleResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RoleBulkAction(BaseModel):
    role_ids: list[UUID] = Field(
        ...,
        min_length=1
    )


class RoleBulkActionResponse(BaseModel):
    activated_roles: list[dict] = Field(default_factory=list)
    already_active_roles: list[dict] = Field(default_factory=list)

    deactivated_roles: list[dict] = Field(default_factory=list)
    already_inactive_roles: list[dict] = Field(default_factory=list)