from typing import Optional, Tuple
from app.core.utils import JwtService
import jwt
from starlette.authentication import AuthenticationBackend
from starlette.middleware.authentication import (
    AuthenticationMiddleware as BaseAuthenticationMiddleware,
)
from starlette.requests import HTTPConnection
from app.models import User
from app.schemas.auth_schemas import CurrentUser
from app.core.db import get_async_session
from sqlalchemy import select
from uuid import UUID

# @standalone_session
async def get_user_by_id(user_id: str) -> User:
    try:
        valid_uuid = UUID(user_id)
    except ValueError:
        print("Invalid UUID format")
        return None
    async with get_async_session() as session:
        query = select(User).where(User.id == valid_uuid)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
    return user


class AuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection) -> Tuple[bool, Optional[CurrentUser]]:
        # current_user = None
        current_user = CurrentUser()
        authorization: str = conn.headers.get("Authorization")
        if not authorization:
            return False, current_user

        try:
            scheme, credentials = authorization.split(" ")
            if scheme.lower() != "bearer":
                return False, current_user
        except ValueError:
            return False, current_user

        if not credentials:
            return False, current_user

        try:
            payload = await JwtService().verify_token(credentials)
            user_id = payload.get("user_id")
            if user_id is None:
                return False, current_user
        except Exception as e:
            return False, current_user
        
        
        current_user.user = await get_user_by_id(user_id)
        if current_user.user is None:
            return False, current_user

        return True, current_user.user


class AuthenticationMiddleware(BaseAuthenticationMiddleware):
    pass
