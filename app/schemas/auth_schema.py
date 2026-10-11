from uuid import UUID
from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str



class CurrentUserResponse(BaseModel):
    id: UUID
    company_id: UUID | None
    branch_id: UUID | None
    company_name: str | None = None
    branch_name: str | None = None
    role_id: UUID
    role_name: str
    first_name: str
    last_name: str | None
    email: EmailStr
    phone: str | None
    is_active: bool
