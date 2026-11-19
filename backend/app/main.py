from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.database.session import check_database_connection, get_db
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.users import router as users_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API do sistema OrdemFácil.",
    version="0.1.0",
    openapi_url="/openapi.json" if settings.app_debug else None,
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

register_exception_handlers(app)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)


@app.get("/health", include_in_schema=False)
def root_health(db: Session = Depends(get_db)) -> dict[str, str]:
    check_database_connection(db)
    return {"status": "ok"}
