from fastapi import APIRouter

from app.api.auth_routers.routes import auth_router
from app.api.file_uploads.routes import file_router
from app.api.user_extra.routes import user_router


router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(file_router, prefix="/files", tags=["File Processing"])
router.include_router(user_router, prefix="/user", tags=["User Details"])

__all__ = ["router"]
