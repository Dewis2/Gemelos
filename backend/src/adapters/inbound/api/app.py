from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from adapters.inbound.api.container import ApplicationContainer
from adapters.inbound.api.routes import router
from infrastructure.config import Settings, get_settings
from infrastructure.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            app.state.container.close()

    app = FastAPI(
        lifespan=lifespan,
        title=resolved.app_name,
        version="0.1.0",
        description="API PoC; no contiene resultados experimentales ni datos locales 2026.",
    )
    app.state.container = ApplicationContainer(resolved)

    @app.exception_handler(IntegrityError)
    async def integrity_error(_request, _exc):
        return JSONResponse(
            status_code=409,
            content={
                "detail": "La operación viola una referencia o restricción de la base de datos."
            },
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
