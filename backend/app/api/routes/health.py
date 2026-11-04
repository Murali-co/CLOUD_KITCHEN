from fastapi import APIRouter
from app.core.config import settings
from app.db.database import check_db_connectivity
from app.db.redis import redis_client
from app.schemas.health import HealthResponse, ServiceStatus

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Evaluates API readiness, MySQL primary database connectivity,
    and Redis in-memory cache connectivity.
    """
    db_status = check_db_connectivity()
    redis_status = redis_client.ping()

    if db_status.get("available") and redis_status.get("available"):
        overall = "healthy"
    elif db_status.get("available"):
        overall = "degraded"
    else:
        overall = "unhealthy"

    return HealthResponse(
        api_status=overall,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        mysql=ServiceStatus(
            status=db_status.get("status", "unknown"),
            available=db_status.get("available", False),
            detail=db_status.get("detail", ""),
        ),
        redis=ServiceStatus(
            status=redis_status.get("status", "unknown"),
            available=redis_status.get("available", False),
            detail=redis_status.get("detail", ""),
        ),
    )
