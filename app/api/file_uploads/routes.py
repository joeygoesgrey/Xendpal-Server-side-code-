from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
from app.models import File, Chunk, User, Folder
from app.core.db import AsyncTransactional, get_async_session 
from app.core.exceptions import UnauthorizedException
from fastapi import UploadFile, Form
from fastapi import File as fastapi_File
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.api.file_uploads.tasks import retrieve_and_trigger_celery
from fastapi.responses import FileResponse
from pydantic import UUID4
from typing import Optional

file_router = APIRouter()
 

@file_router.post("/upload-chunk")
async def upload_chunk(
    request: Request,
    background_tasks: BackgroundTasks,
    file_data: UploadFile=Form(...),
    file_name: str=Form(...),
    total_file_size: int=Form(...),
    sequence_number: int=Form(...),
    total_chunks: int=Form(...),
    is_complete: bool=Form(...),
    file_type: str=Form(...),
    folder_id: Optional[UUID4]=Form(default=None)
):
    current_user = request.user
    if not current_user:
        raise UnauthorizedException()
    folder_db = None
    print(folder_id)
    try:
        if folder_id:
            async with get_async_session() as session:
                folder_db = await session.execute(
                    select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
                )
                folder_db = folder_db.scalar_one_or_none()

        async with get_async_session() as session:
            file_db = await session.execute(
                select(File).where(File.file_name == file_name, File.user_id == current_user.id)
            )
            file_db = file_db.scalar_one_or_none()

            if not file_db:
                file_db = File(
                    user_id=current_user.id,
                    file_name=file_name,
                    size=total_file_size,
                    total_chunks=total_chunks,
                    is_complete=False,
                    file_type=file_type,
                    folder_id=folder_id if folder_db is not None else None
                )
                session.add(file_db)
                await session.flush()

            chunk_db = Chunk(
                file_id=file_db.file_id,
                sequence_number=sequence_number,
                data=await file_data.read(),
                is_received=True
            )
            session.add(chunk_db)

            if is_complete and sequence_number == total_chunks - 1:
                file_db.is_complete = True
                user_db = await session.execute(select(User).where(User.id == current_user.id))
                user_db = user_db.scalar_one()
                user_db.space += total_file_size

                background_tasks.add_task(retrieve_and_trigger_celery, {"file_id": file_db.file_id, "file_name": file_db.file_name})
                await session.commit()

                return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "File upload completed successfully"})

            await session.commit()
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"detail": "Chunk uploaded successfully"})

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@file_router.delete("/delete-file/{file_id}")
@AsyncTransactional()
async def delete_file(request: Request, file_id: int):
    current_user = request.user
    if current_user:
        async with get_async_session() as session:
            # Retrieve the file record
            file_result = await session.execute(select(File).filter(File.file_id == file_id))
            file_db = file_result.scalar_one_or_none()
            
            if not file_db:
                raise HTTPException(status_code=404, detail="File not found")

            # Retrieve the user record
            user_result = await session.execute(select(User).filter(User.id == current_user.id))
            user_db = user_result.scalar_one()

            # Update user's space used
            if user_db.space - file_db.size >= 0:
                user_db.space -= file_db.size
            else:
                # Reset to 0 if subtraction goes below 0 (edge case handling)
                user_db.space = 0

            # Delete the file from the database
            await session.delete(file_db)
            await session.commit()

            # Add code here to delete the file from the server's storage if necessary
            # Handle any errors that may occur during file deletion

            return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "File deleted successfully"})
    else:
        raise UnauthorizedException()
