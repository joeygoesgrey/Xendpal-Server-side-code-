from pydantic import BaseModel, Field,  EmailStr
from typing import Optional
from uuid import UUID


class RefreshToken(BaseModel):
    access_token: str = Field(..., description="Token")
    refresh_token: str = Field(..., description="Refresh token")


class VerifyToken(BaseModel):
    access_token: str = Field(..., description="Access Token")

class User(BaseModel):
    id: UUID
    email:  EmailStr
    sub: str
    name: str
    picture: str
    space: int
    max_space: int = 524288000
    password: str

class CurrentUser(BaseModel):
    user: Optional[User] = None  # Add a user attribute

    class Config:
        from_attributes = True


class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")
