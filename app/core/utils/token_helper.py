from datetime import datetime, timedelta
import jwt
from app.core.config import config
from app.core.exceptions import DecodeTokenException, ExpiredTokenException
from app.schemas.auth_schemas import RefreshToken

class TokenHelper:
    @staticmethod
    def encode(payload: dict, expire_period: int, is_access_token: bool = True) -> str:
        expire_time = timedelta(minutes=expire_period) if is_access_token else timedelta(days=expire_period)
        token = jwt.encode(
            payload={**payload, "exp": datetime.utcnow() + expire_time},
            key=config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )
        return token

    @staticmethod
    def decode(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                config.JWT_ALGORITHM,
                verify_expiration=True,
            )
        except jwt.exceptions.DecodeError:
            raise DecodeTokenException
        except jwt.exceptions.ExpiredSignatureError:
            raise ExpiredTokenException



class JwtService:
    async def verify_token(self, token: str) -> dict:
        return TokenHelper.decode(token=token)

    async def create_refresh_token(self, refresh_token: str) -> RefreshToken:
        try:
            decoded_refresh_token = TokenHelper.decode(
                token=refresh_token,
            )
            if decoded_refresh_token.get("sub") != "refresh":
                raise DecodeTokenException

            new_access_token = TokenHelper.encode(
                payload={"user_id": decoded_refresh_token.get("user_id")},
                expire_period=config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            new_refresh_token = TokenHelper.encode(
                payload={"sub": "refresh", "user_id": decoded_refresh_token.get("user_id")},
                expire_period=config.REFRESH_TOKEN_EXPIRE_DAYS,
                is_access_token=False
            )
            return RefreshToken(
                access_token=new_access_token,
                refresh_token=new_refresh_token
            )
        except jwt.exceptions.DecodeError:
            raise DecodeTokenException

 