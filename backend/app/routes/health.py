from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import check_database_connection, get_db

router = APIRouter(tags=["sistema"])


@router.get("/health", summary="Verificação de saúde da aplicação")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    check_database_connection(db)
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }
