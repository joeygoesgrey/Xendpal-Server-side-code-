import asyncio
from sqlalchemy import select
from app.models import Chunk
from app.core.celery_config import celery_app
from pathlib import Path
from app.core.db import get_async_session


# In your FastAPI background task function
async def retrieve_and_trigger_celery(params):
    file_id = params.get("file_id")
    file_name = params.get("file_name")
    async with get_async_session() as session:
        result = await session.execute(
            select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.sequence_number)
        )
        chunks = result.scalars().all()

    # Ensure that chunk.data is in bytes format
    chunks_data = [chunk.data if isinstance(chunk.data, bytes) else bytes(chunk.data) for chunk in chunks]
    rebuild_file.delay(file_id, file_name, chunks_data)


# In your Celery taskSELE
@celery_app.task
def rebuild_file(file_id, file_name, chunks_data):
    # Join the bytes-like objects in chunks_data
    file_data = b''.join(chunks_data)

    root_dir = Path(__file__).parent.parent.parent.parent
    uploads_path = root_dir / 'Uploads'
    uploads_path.mkdir(parents=True, exist_ok=True)
    file_path = uploads_path / f"{file_id}-{file_name}"

    with open(file_path, 'wb') as file:
        file.write(file_data)

    return {"status": "File rebuilt successfully"}
