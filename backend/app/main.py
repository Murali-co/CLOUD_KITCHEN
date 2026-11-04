import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.db.database import check_db_connectivity
from app.db.redis import redis_client

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloud_kitchen_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    
    # Non-blocking connectivity checks
    db_check = check_db_connectivity()
    logger.info(f"MySQL Status: {db_check['status']} - {db_check['detail']}")

    redis_check = redis_client.ping()
    logger.info(f"Redis Status: {redis_check['status']} - {redis_check['detail']}")

    yield

    # Clean shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    redis_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready REST API for Cloud Kitchen Management & Online Food Ordering System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration for React/Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly without leaking internal structures."""
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Input validation failed",
            "errors": error_messages,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Sanitizes raw database exceptions so internal credentials/queries are never leaked."""
    logger.error(f"Database error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "A database error occurred while processing your request. Please try again later.",
            "errors": ["Internal database failure"],
        },
    )


@app.get("/", tags=["Root"])
def root():
    """Root entrypoint returning application status and documentation URL."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


# Include unified API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
