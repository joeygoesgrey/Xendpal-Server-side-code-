from typing import List
from fastapi import APIRouter, Request, HTTPException
from app.models import File, Chunk
from app.core.db import AsyncTransactional,  get_async_session
from app.core.exceptions import UnauthorizedException
from fastapi import UploadFile, Form
from fastapi import File as fastapi_File
from sqlalchemy import select
from app.api.file_uploads.tasks import rebuild_file
from fastapi.responses import FileResponse
import os



file_router = APIRouter()
 

@file_router.post("/upload-chunk")
@AsyncTransactional()
async def upload_chunk(
    request: Request,
    file_data: UploadFile = fastapi_File(...),
    file_name: str = Form(...),
    total_file_size: int = Form(...),
    sequence_number: int = Form(...),
    total_chunks: int = Form(...),
    is_complete: bool = Form(...),
    file_type: str = Form(...),
):
    print(
        f"file_name: {file_name}\n"
        f"total_file_size: {total_file_size}\n"
        f"sequence_number: {sequence_number}\n"
        f"total_chunks: {total_chunks}\n"
        f"file_type: {file_type}\n"
        f"is_complete: {is_complete}\n"
    )
    current_user = request.user
    if current_user:
        try:
            file_bytes = await file_data.read()  # Read the contents of the uploaded file

            async with get_async_session() as session:
                # Create or retrieve the corresponding File record in the database
                file_db = await session.execute(
                    select(File).where(
                        File.file_name == file_name,
                        File.user_id == current_user.id
                    )
                )
                file_db = file_db.scalar_one_or_none()

                if not file_db:
                    # If the File record doesn't exist, create it
                    file_db = File(
                        user_id=current_user.id,
                        file_name=file_name,
                        size=total_file_size,
                        total_chunks=total_chunks,
                        is_complete=False,
                        file_type=file_type,
                    )
                    session.add(file_db)
                    await session.flush()  # Ensure file_db is updated with the generated ID

                # Create a Chunk record for the received chunk
                chunk_db = Chunk(
                    file_id=file_db.file_id,
                    sequence_number=sequence_number,
                    data=file_bytes,  # Use the raw bytes of the file
                    is_received=True
                )

                session.add(chunk_db)

                if is_complete and sequence_number == total_chunks - 1:
                    # If this is the last chunk, mark the File record as complete
                    file_db.is_complete = True
                    params = {
                        "file_id": file_db.file_id,
                        "file_type": file_db.file_type,
                        "file_name": file_db.file_name,
                    }
                    # result = await rebuild_file(params)
                  
                    rebuild_file.delay(params)

                await session.commit()  # Commit the transaction

            return {"message": "Chunk uploaded successfully"}

        except Exception as e:
            # Handle any database or processing errors here
            print(f"Exception from routes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise UnauthorizedException()


@file_router.get("/{file_id}/{file_name}")
async def download_file(file_id: str, file_name: str):
    file_path = f"Uploads/{file_id}-{file_name}"
    if os.path.exists(file_path):
        print(file_path)
        return FileResponse(file_path, media_type="application/pdf")
    else:
        return {"error": "File not found"}


# http://localhost:8080/files/60/Teaching%20the%20science%20of%20learning.pdf

@file_router.delete("/delete-file/{file_id}")
@AsyncTransactional()
async def delete_file(request: Request, file_id: int):
    current_user = request.user
    if current_user:
        # Check if the file with the provided ID exists
        async with get_async_session() as session:
            # Use select to query the File model
            file_db = await session.execute(select(File).filter(File.file_id == file_id))
            file_db = file_db.scalar_one_or_none()
            
            if not file_db:
                raise HTTPException(status_code=404, detail="File not found")

            # Delete the file from the database
            await session.delete(file_db)  # Await the deletion
            await session.commit()

            # You can also add code here to delete the corresponding file from the server's storage
            # Make sure to handle any errors that may occur during file deletion

            return {"message": "File deleted successfully"}
    else:
        raise UnauthorizedException()