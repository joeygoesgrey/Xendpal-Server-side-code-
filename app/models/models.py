from sqlalchemy import Column, String, Integer, Boolean
from app.core.db.mixins import TimestampMixin
from sqlalchemy.future import select
from app.core.db import Base
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    LargeBinary,
    UUID,
)
from sqlalchemy.orm import relationship
import uuid
from app.core.db import get_async_session

def generate_uuid():
    return str(uuid.uuid4())
 

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    sub = Column(String)
    name = Column(String)
    picture = Column(String)
    space = Column(Integer, default=0)  # Current space used
    max_space = Column(BigInteger, default=524288000)
    password = Column(String)
    files = relationship("File", back_populates="owner")  # Relationship to files

    @staticmethod
    async def get_user_by_email(email: str) -> "User":
        async with get_async_session() as s:
            result = await s.execute(select(User).where(User.email == email))
            return result.scalars().first()
     

class File(Base, TimestampMixin):
    __tablename__ = 'files'
    file_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Use UUID data type
    file_name = Column(String, index=True)
    total_chunks = Column(Integer)
    is_complete = Column(Boolean, default=False)
    size = Column(BigInteger)  # Add this line for the size of the file in bytes
    file_type = Column(String, nullable=True)  # New column for file type


    owner = relationship("User", back_populates="files")  # Relationship to User
    chunks = relationship("Chunk", back_populates="file")



class Chunk(Base, TimestampMixin):
    __tablename__ = 'chunks'
    chunk_id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.file_id'))
    sequence_number = Column(Integer)
    data = Column(LargeBinary)
    is_received = Column(Boolean, default=False)

    file = relationship("File", back_populates="chunks")  # Corrected relationship

 