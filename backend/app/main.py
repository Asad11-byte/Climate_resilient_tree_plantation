from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, environment, health, retrieve, species
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Location-aware, evidence-grounded RAG API for climate-resilient "
            "tree plantation recommendations in Mandi Bahauddin, Punjab."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(retrieve.router, prefix=settings.api_prefix)
    app.include_router(chat.router, prefix=settings.api_prefix)
    app.include_router(species.router, prefix=settings.api_prefix)
    app.include_router(environment.router, prefix=settings.api_prefix)
    # Phase 5+ routers (live environmental-data ingestion, location, documents
    # CRUD) are registered here as they're built — see docs/architecture.md.

    return app


app = create_app()
