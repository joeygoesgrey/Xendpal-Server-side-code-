from app.core.celery_config import celery_app
from app.models import Chunk
from app.core.db import get_sync_session
from pathlib import Path
from sqlalchemy import select

@celery_app.task
def rebuild_file(params: dict):
    try:
        file_id = params.get("file_id")
        file_type = params.get("file_type")
        file_name = params.get("file_name")
        
        # Synchronously retrieve chunks
        chunks = None
        with next(get_sync_session()) as session:
            result = session.execute(
                select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.sequence_number)
            )
            chunks = result.scalars().all()
        print(chunks)

        file_data = b''.join([chunk.data for chunk in chunks])

        # Rest of the file handling remains the same
        root_dir = Path(__file__).parent.parent.parent.parent
        uploads_path = root_dir / 'Uploads'
        uploads_path.mkdir(parents=True, exist_ok=True)

        file_path = uploads_path / f"{file_id}-{file_name}"
        with open(file_path, 'wb') as file:
            file.write(file_data)

        return {"status from task": "Great task done"}
    except Exception as e:
        return {"error from task": str(e)}

# from app.core.celery_config import celery_app
# from app.models import Chunk
# from app.core.db import get_sync_session 
# from pathlib import Path
# from sqlalchemy import select
# import asyncio

# # This is the synchronous wrapper for your asynchronous task
# @celery_app.task
# def rebuild_file(params: dict):
#     try:
#         loop = asyncio.get_event_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#     return loop.run_until_complete(_rebuild_file_async(params))

# async def _rebuild_file_async(params: dict):
#     try:
#         file_id = params.get("file_id")
#         file_type = params.get("file_type")
#         file_name = params.get("file_name")
#         chunks = None
#         async with async_session() as session:
#             result = await session.execute(
#                 select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.sequence_number)
#             )
#             chunks = result.scalars().all()
#         print(chunks)
#         file_data = b''.join([chunk.data for chunk in chunks])

#         root_dir = Path(__file__).parent.parent.parent.parent
#         uploads_path = root_dir / 'Uploads'
#         uploads_path.mkdir(parents=True, exist_ok=True)

#         file_path = uploads_path / f"{file_id}-{file_name}"
#         with open(file_path, 'wb') as file:
#             file.write(file_data)

#         return {"status from task": "Great task done"}
#     except Exception as e:
#         # Return an error message as a JSON serializable dictionary
#         return {"error from task": str(e)}


 
# # DELETE FROM chunks;



