from typing import List

from fastapi import FastAPI, Request, Depends
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.core.config import config
from app.core.exceptions import CustomException
from app.core.dependencies import Logging
from app.core.middlewares import (
    AuthenticationMiddleware,
    AuthBackend,
    SQLAlchemyMiddleware,
    ResponseLogMiddleware,
)


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router)


def init_listeners(app_: FastAPI) -> None:
    # Exception handler
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.code,
            content={"success": exc.success, "message": exc.message},
        )


def on_auth_error(request: Request, exc: Exception):
    status_code, success, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        success = exc.success
        message = exc.message

    return JSONResponse(
        status_code=status_code,
        content={"success": success, "message": message},
    )


def make_middleware() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(
            AuthenticationMiddleware,
            backend=AuthBackend(),
            on_error=on_auth_error,
        ),
        Middleware(SQLAlchemyMiddleware),
        Middleware(ResponseLogMiddleware),
    ]
    return middleware
 
def create_app() -> FastAPI:
    app_ = FastAPI(
        title="Xendpal",
        description="Xendpal API",
        version="1.0.0",
        docs_url=None if config.ENV == "production" else "/docs",
        redoc_url=None if config.ENV == "production" else "/redoc",
        dependencies=[Depends(Logging)],
        middleware=make_middleware(),
    )

    # Mount the "uploads" directory as a static folder
    app_.mount("/Uploads", StaticFiles(directory="Uploads"), name="uploads")

    init_routers(app_=app_)
    init_listeners(app_=app_)
    return app_


app = create_app()
