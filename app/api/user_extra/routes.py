from app.core.config import config
from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.schemas.api_v2_schemas import UserBase
from app.models import User, File
from app.core.db import async_session, Transactional
from app.core.exceptions import UnauthorizedException
import datetime
from sqlalchemy import func, extract, select
from sqlalchemy.ext.asyncio import AsyncSession


user_router = APIRouter()


CLIENT_ID = config.CLIENT_ID
CLIENT_SECRET = config.CLIENT_SECRET
REDIRECT_URI = config.REDIRECT_URI
TOKEN_URL = config.TOKEN_URL
USER_INFO_URL = config.USER_INFO_URL
 
@user_router.get("/google_redirect")
async def login():
    """
    Takes the user to the google callback 
    """
    # Constructing the authorization URL for Google's OAuth2
    authorization_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=email+profile"
    return RedirectResponse(authorization_url)



@user_router.get("/info", response_model=UserBase)
@Transactional()
async def get_user_information(request: Request):
    current_user = request.user
    if current_user:
        async with async_session() as session:
            # Use the select construct for the query
            stmt = select(User).where(User.id == current_user.id)
            result = await session.execute(stmt)
            user_info = result.scalar_one_or_none()
            return user_info
    else:
        raise UnauthorizedException()


@user_router.get("/get-yearly-usage",)
async def get_yearly_usage(request: Request):
    """
    Retrieves the total size of uploaded files for each month of the current year, for the authenticated user.

    Parameters:
    - current_user: the authenticated user, obtained from the access token

    Returns:
    - A dictionary containing two lists: the months (as strings) and the corresponding total usage (in bytes) for each month

    Raises:
    - None
    """
    current_user = request.user
    if current_user:
        async with async_session() as db:
            yearly_usage = await db.execute(
                select(
                    extract("month", File.created_at).label("month"),
                    func.sum(File.size).label("total_size")
                )
                .where(
                    File.user_id == current_user.id,
                    extract("year", File.created_at) == datetime.datetime.now().year
                )
                .group_by(extract("month", File.created_at))
            )

            result = yearly_usage.all()

        months = [str(record.month) for record in result]
        usages = [record.total_size for record in result]

        return {"month": months, "usage": usages}
    else:
        raise UnauthorizedException



@user_router.get("/items")
async def get_user_files(
    request: Request,
    session: AsyncSession = Depends(async_session)
):
    current_user = request.user
    if current_user:
            
        try:
            async with session.begin():
                # Query for all files for the current user
                result = await session.execute(
                    select(File).where(File.user_id == current_user.id)
                )
                user_files = result.scalars().all()

                # Transform the file records to JSON serializable format
                files_info = [
                    {
                        "file_id": file.file_id,
                        "file_name": file.file_name,
                        "size": file.size, 
                        "file_type": file.file_type,
                        "created_at": file.created_at,
                        
                    }
                    for file in user_files
                ]

                return files_info

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise UnauthorizedException