"""FastAPI application entrypoint for AI Business Architect."""

import logging
import os
import time
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router, health_router
from app.config import get_settings
from app.core.exceptions import AppException
from app.logging_config import configure_logging

# Configure logging at startup
settings = get_settings()
configure_logging(level=settings.log_level)
logger = logging.getLogger("app.main")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Turn your business idea into an actionable blueprint with AI-assisted business modelling and tech stack recommendations.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
origins = settings.parsed_cors_origins or ["http://localhost:5173", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    """Inject request correlation IDs, measure processing latency, and set secure response headers."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start_time

    # Set response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Domain Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        f"Handled application exception: {exc.code} - {exc.message}",
        extra={"extra_fields": {"request_id": request_id, "code": exc.code, "details": exc.details}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


# Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    formatted_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        formatted_errors.append(f"{loc}: {err.get('msg')}")

    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {formatted_errors}",
        extra={"extra_fields": {"request_id": request_id, "errors": formatted_errors}},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request payload failed validation.",
                "details": {"validation_errors": formatted_errors},
            },
        },
    )


# Unhandled Exception Handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unhandled server error on {request.method} {request.url.path}",
        exc_info=True,
        extra={"extra_fields": {"request_id": request_id}},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {"request_id": request_id},
            },
        },
    )


# Include API and Health Routers
app.include_router(health_router)
app.include_router(api_router)


# Production Single-Origin Static File & SPA Routing
# Checks for built frontend assets in standard locations (Docker / local build)
dist_candidates = [
    Path(__file__).resolve().parent.parent / "static",  # Docker production location: /app/static
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",  # Local dev build: frontend/dist
]

static_dist_path: Path | None = None
for candidate in dist_candidates:
    if candidate.exists() and (candidate / "index.html").exists():
        static_dist_path = candidate
        break

if static_dist_path:
    assets_dir = static_dist_path / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    logger.info(f"Mounted production frontend static assets from: {static_dist_path}")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Exclude API, health, docs routes from SPA catch-all
        if (
            full_path.startswith("api")
            or full_path.startswith("health")
            or full_path.startswith("ready")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi.json")
        ):
            return JSONResponse(status_code=404, content={"success": False, "error": {"code": "NOT_FOUND", "message": "Not found"}})

        # Check if requesting a direct static file from dist root (e.g. favicon.ico, vite.svg)
        file_path = static_dist_path / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)

        # Fallback to SPA index.html for client-side routing
        return FileResponse(static_dist_path / "index.html")
