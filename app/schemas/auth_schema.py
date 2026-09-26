from uuid import UUID
from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUserResponse(BaseModel):
    id: UUID
    company_id: UUID
    role_id: UUID
    first_name: str
    last_name: str | None
    email: EmailStr
    phone: str | None
    is_active: bool

