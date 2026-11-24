from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.modules.cv.router import router as cv_router
from app.modules.jobs.router import router as jobs_router
from app.modules.profile.router import router as profile_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.site_check.router import router as site_check_router
from app.shared.exceptions import AppException

app = FastAPI(title="Job Scraper")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    """Map custom exceptions to {"detail": message}."""
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


api = APIRouter(prefix="/api")


@api.get("/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}


api.include_router(jobs_router)
api.include_router(profile_router)
api.include_router(cv_router)
api.include_router(recommendations_router)
api.include_router(site_check_router)
app.include_router(api)
