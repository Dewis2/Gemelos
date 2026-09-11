from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.api.container import ApplicationContainer
from adapters.inbound.api.routes import router
from infrastructure.config import Settings, get_settings
from infrastructure.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="API PoC; no contiene resultados experimentales ni datos locales 2026.",
    )
    app.state.container = ApplicationContainer(resolved)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
