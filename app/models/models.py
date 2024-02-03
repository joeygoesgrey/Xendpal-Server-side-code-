from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    BigInteger,
    Boolean,
    LargeBinary,
)
from sqlalchemy.orm import relationship, backref
from app.core.db import get_async_session
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base
import uuid
from app.core.db.mixins import TimestampMixin
from sqlalchemy.future import select

 
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
    # Ensure folders and files are deleted when the user is deleted
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")


class Folder(Base, TimestampMixin):
    __tablename__ = 'folders'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('folders.id'), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    # Set up relationships
    owner = relationship("User", back_populates="folders")
    subfolders = relationship("Folder",
                              backref=backref('parent', remote_side=[id]),
                              cascade="all, delete-orphan")
    files = relationship("File", back_populates="folder", cascade="all, delete-orphan")


class File(Base, TimestampMixin):
    __tablename__ = 'files'
    file_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    folder_id = Column(UUID(as_uuid=True), ForeignKey('folders.id'), nullable=True)
    file_name = Column(String, index=True)
    total_chunks = Column(Integer)
    is_complete = Column(Boolean, default=False)
    size = Column(BigInteger)
    file_type = Column(String, nullable=True)
    # Ensure chunks are deleted when the file is deleted
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")  
    owner = relationship("User", back_populates="files")
    folder = relationship("Folder", back_populates="files")


class Chunk(Base, TimestampMixin):
    __tablename__ = 'chunks'
    chunk_id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.file_id'))
    sequence_number = Column(Integer)
    data = Column(LargeBinary)
    is_received = Column(Boolean, default=False)
    # Link back to the file
    file = relationship("File", back_populates="chunks")
 