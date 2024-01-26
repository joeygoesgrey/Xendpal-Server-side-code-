from fastapi import APIRouter, Response, Depends, status, HTTPException 
from app.core.config import config
from app.schemas.auth_schemas import RefreshToken, RefreshTokenSchema
from app.core.utils import JwtService, Verify_password, Hash_password, TokenHelper
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.db import async_session
from app.models import User
from app.schemas.api_v2_schemas import GoogleLoginRequest, EmailValidate
import httpx
from app.core.exceptions import ForbiddenException  # Import the custom exception
from sqlalchemy.future import select


CLIENT_ID = config.CLIENT_ID
CLIENT_SECRET = config.CLIENT_SECRET
REDIRECT_URI = config.REDIRECT_URI
TOKEN_URL = config.TOKEN_URL
USER_INFO_URL = config.USER_INFO_URL


auth_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username  # Treated 'username' as 'email'
    password = form_data.password
    if email and password:
        try:
            user_email = EmailValidate(email=email)  
        except Exception as e:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
        # Query the User model to check if the email exists
        user = await User.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
        # Check if the provided password matches the stored password
        if not Verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
        
        # Generate access and refresh tokens
        return {"access_token": TokenHelper.encode(
                payload={"user_id": user.id},
                expire_period=config.ACCESS_TOKEN_EXPIRE_MINUTES
            ), "refresh_token": TokenHelper.encode(
                payload={"sub": "refresh", "user_id": user.id},
                expire_period=config.REFRESH_TOKEN_EXPIRE_DAYS,
                is_access_token=False
            ), "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )


async def get_current_user(request: str):
    try:
        # Extracting the authorization code from the request's query parameters
        authorization_code = request

        # Preparing the data to exchange the authorization code for an access token
        token_data = {
            "code": authorization_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        # Creating an HTTP client
        async with httpx.AsyncClient() as client:
            # Sending a POST request to exchange the authorization code for an access token
            token_response = await client.post(TOKEN_URL, data=token_data)
            token_response.raise_for_status()  # Checking for HTTP errors
            token_info = token_response.json()  # Parsing the JSON response

            # Extracting the access token
            access_token = token_info["access_token"]

            # Sending a GET request to fetch the user's information using the access token
            user_response = await client.get(
                USER_INFO_URL, headers={
                    "Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()  # Checking for HTTP errors
            user_info = user_response.json()  # Parsing the JSON response
        print(user_info)
        return user_info  # Returning the user's information

    except httpx.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

    return None  # Return None or some default value if an error occurs



@auth_router.post(
    "/login/google",
    response_model=RefreshToken,
)
async def login_callback(
    request: GoogleLoginRequest,
):
    current_user = await get_current_user(request.code)
    if current_user is not None:
        async with async_session() as session:
            stmt = select(User).filter_by(email=current_user.get("email"))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            # Check if user already exists, if not, create a new user
            if not user:
                new_user = User(
                    email=current_user.get("email"),
                    sub=current_user.get("sub"),
                    name=current_user.get("name"),
                    picture=current_user.get("picture"),
                )
                session.add(new_user)
                await session.commit()  # Explicitly commit the session to save the new user
                user_id = new_user.id  # Use new_user.id for the token generation
            else:
                user_id = user.id  # Use existing user.id for the token generation

            # Generate access and refresh tokens
            access_token = TokenHelper.encode(
                payload={"user_id": str(user_id)},
                expire_period=config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            refresh_token = TokenHelper.encode(
                payload={"sub": "refresh", "user_id": str(user_id)},
                expire_period=config.REFRESH_TOKEN_EXPIRE_DAYS,
                is_access_token=False
            )
            return {"access_token": access_token, "refresh_token": refresh_token }
    else:
        raise ForbiddenException()




@auth_router.post(
    "/refresh-token",
    response_model=RefreshToken,
)
async def refresh_token(request: RefreshTokenSchema):
    token = await JwtService().create_refresh_token(
     refresh_token=request.refresh_token
    )
    return {"access_token": token.access_token, "refresh_token": token.refresh_token}

