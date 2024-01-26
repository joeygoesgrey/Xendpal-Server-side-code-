from pydantic import BaseModel, Field, EmailStr, constr, conint
from typing import Optional, List
from datetime import datetime
 
class FileChunk(BaseModel):
    file_name: str = Field(..., description="Name of the Uploaded file")
    total_file_size: int = Field(..., description="Total file size of the Uploaded file")
    sequence_number: int = Field(..., description="Sequence number of the Chunked Uploaded file")
    total_chunks: int = Field(..., description="Total chunks to be uploaded from the frontend")
    file_data: bytes = Field(..., description="Blob bytes of the Uploaded file")
    is_complete: bool = Field(..., description="A Bool flag to indicate if the entire chunk has been uploaded")
    file_type : str = Field(..., description="File type")


class EmailValidate(BaseModel):
    email: EmailStr


class GoogleLoginRequest(BaseModel):
    code: str


class UserBase(BaseModel):
    name: str
    picture: str
    space: int
    max_space: int

    class Config:
        from_attributes = True


class UploadModelSchema(BaseModel):
    id: str
    name: str
    path: str
    type: str
    created_at: datetime
    size: int
    owner_id: EmailStr

    class Config:
        from_attributes = True



class Usage(BaseModel):
    months: List[str]  # Allow empty strings
    usages: List[int]  # Allow zero or positive integers


# class Usage(BaseModel):
#     months: Optional[List[constr(min_length=1)]]
#     usages: Optional[List[conint(ge=0)]]