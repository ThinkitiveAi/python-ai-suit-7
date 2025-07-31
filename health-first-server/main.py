from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from contextlib import asynccontextmanager
import time
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import create_tables
from app.controllers.provider_controller import router as provider_router
from app.controllers.auth_controller import router as auth_router

from app.controllers.patient_controller import router as patient_router
from app.controllers.availability_controller import router as availability_router
from app.middlewares.rate_limiting import rate_limit_middleware
from app.middlewares.validation import validation_middleware_handler
from app.schemas.patient_schema import ValidationErrorResponse

from app.middlewares.rate_limiting import rate_limit_middleware
from app.middlewares.validation import validation_middleware_handler



# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)
logger.add(
    settings.log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    rotation="10 MB",
    retention="30 days",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Provider Registration API...")

    # Create database tables if using SQL database
    if settings.database_type in ["postgresql", "mysql"]:
        try:
            create_tables()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")

    logger.info(
        f"Provider Registration API started successfully on {settings.app_name} v{settings.app_version}"
    )

    yield

    # Shutdown
    logger.info("Shutting down Provider Registration API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A secure and comprehensive provider registration API with email verification",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure appropriately for production
)

# Add custom middleware
app.middleware("http")(validation_middleware_handler)
app.middleware("http")(rate_limit_middleware)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "INTERNAL_ERROR",
        },
    )



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = {}
    for error in exc.errors():
        field = error["loc"][-1] if error["loc"] else "unknown"
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])

    return JSONResponse(
        status_code=422,
        content=ValidationErrorResponse(
            success=False, message="Validation failed", errors=errors
        ).dict(),
    )


# Include routers
app.include_router(provider_router)
app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(availability_router)

# Include routers
app.include_router(provider_router)
app.include_router(auth_router)



# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Provider Registration API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/provider/health",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "database_type": settings.database_type,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
