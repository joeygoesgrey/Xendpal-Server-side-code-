from pathlib import Path
from app.core.config import config
from fastapi import Request, APIRouter, Depends, HTTPException, status 
from fastapi.responses import RedirectResponse, JSONResponse
from app.schemas.api_v2_schemas import UserBase, FolderSchemaRequest, UserFoldersResponse
from app.models import User, File, Folder
from app.core.db import get_async_session, AsyncTransactional
from app.core.exceptions import UnauthorizedException
import datetime
from sqlalchemy import func, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
import shutil
from typing import List, Dict


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
@AsyncTransactional()
async def get_user_information(request: Request):
    current_user = request.user
    if current_user:
        async with get_async_session() as session:
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
        async with get_async_session() as db:
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
        raise UnauthorizedException()


@user_router.get("/items")
@AsyncTransactional()
async def get_user_folders_and_files(
    request: Request,
    session: AsyncSession=Depends(get_async_session)
):
    current_user = request.user
    if not current_user:
        raise UnauthorizedException()

    try:
        async with session.begin():
            # Fetch folders and order by Folder.created_at
            folders_result = await session.execute(
                select(Folder)
                .where(Folder.user_id == current_user.id)
                .order_by(Folder.created_at.desc())  # Corrected to Folder.created_at
            )
            folders = folders_result.scalars().all()

            # Fetch files that do not belong to any folder
            files_result = await session.execute(
                select(File)
                .where(File.user_id == current_user.id, File.folder_id.is_(None))
                .order_by(File.created_at.desc())
            )
            files = files_result.scalars().all()

            # Transform folders to JSON serializable format
            folders_info = [
                {
                    "id": folder.id,
                    "name": folder.name,
                    "created_at": folder.created_at.isoformat(),
                    "type": "folder",
                }
                for folder in folders
            ]

            # Transform files to JSON serializable format
            files_info = [
                {
                    "id": file.file_id,
                    "name": file.file_name,
                    "created_at": file.created_at.isoformat(),
                    "type": "file",
                }
                for file in files
            ]

            # Combine folders and files
            items = folders_info + files_info

            return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.post("/create_folder", status_code=status.HTTP_201_CREATED)
@AsyncTransactional()
async def create_folder(
    schema: FolderSchemaRequest,
    request: Request,
):
    current_user = request.user
    if current_user:
        try:
            async with get_async_session() as session:
                new_folder = Folder(name=schema.name, user_id=current_user.id, parent_id=schema.parent_id)
                session.add(new_folder)
                await session.commit()

                return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Folder created successfully", "folder_id": str(new_folder.id)})
        except Exception as e:
            # Handle specific exceptions for more precise error responses
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    else:
        raise UnauthorizedException()


@user_router.get("/folders", response_model=UserFoldersResponse)
async def read_folders_for_user(
    request: Request,
    db: AsyncSession=Depends(get_async_session),
):
    current_user = request.user
    if current_user is None:
        raise UnauthorizedException()
    async with db as session:
        result = await session.execute(
            select(Folder).where(Folder.user_id == current_user.id)
        )
        folders = result.scalars().all()
        return UserFoldersResponse(folders=folders)


@user_router.delete("/delete_folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
@AsyncTransactional()
async def delete_folder(
    folder_id: str,
    request: Request,
    session: AsyncSession=Depends(get_async_session),
):
    current_user = request.user
    if current_user is None:
        raise UnauthorizedException()
    async with session.begin():
        # Check if the folder exists and belongs to the current user
        query = select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
        result = await session.execute(query)
        folder = result.scalars().first()
        
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found or access denied")
        
        # Delete the folder record from the database
        await session.delete(folder)
        
        # Commit the transaction
        await session.commit()

    return {"message": "Folder deleted successfully"}




@user_router.get("/folders/{folder_id}/files")
async def get_files_in_folder(request: Request, folder_id: str, session: AsyncSession = Depends(get_async_session)) -> List[Dict]:
    current_user = request.user
    if not current_user:
        raise UnauthorizedException()
    
    async with session.begin():
        # Attempt to find the folder to ensure it exists
        folder = await session.get(Folder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Select files associated with the folder
        # files_result = await session.execute(
        #         select(File)
        #         .where(File.user_id == current_user.id, File.folder_id.is_(None))
        #         .order_by(File.created_at.desc())
        # )
        stmt = select(File).where(File.folder_id == folder_id, File.user_id == current_user.id,)
        result = await session.execute(stmt)
        files = result.scalars().all()

        # Manually construct response data
        files_info = [
            {
                "id": file.file_id,
                "name": file.file_name,
                "created_at": file.created_at.isoformat(),
                "type": "file",
            }
            for file in files
        ]

        return files_info