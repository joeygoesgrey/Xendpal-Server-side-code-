from app.core.celery_config import celery_app
from app.models import Chunk
from app.core.db import async_session
from sqlalchemy import select
from pathlib import Path

@celery_app.task
def rebuild_file(params: dict):
    try:
        file_id = params.get("file_id")
        file_type = params.get("file_type")
        file_name = params.get("file_name")
        chunks = None
        with async_session() as session:
            result = session.execute(
                select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.sequence_number)
            )
            chunks = result.scalars().all()
        print(chunks)
        file_data = b''.join([chunk.data for chunk in chunks])

        root_dir = Path(__file__).parent.parent.parent.parent
        uploads_path = root_dir / 'Uploads'
        uploads_path.mkdir(parents=True, exist_ok=True)

        file_path = uploads_path / f"{file_id}-{file_name}"
        with open(file_path, 'wb') as file:
            file.write(file_data)

        return {"status": "Great task done"}    
                

    except Exception as e:
        # Return an error message as a JSON serializable dictionary
        return {"error": str(e)}

 
# DELETE FROM chunks;
