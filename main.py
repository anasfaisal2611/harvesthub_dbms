from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv
import logging
from routes import reports
from database.database import apply_startup_migrations
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

app = FastAPI(
    title="HarvestHUB API",
    description="Agricultural field management with RBAC",
    version="2.0.0",
    swagger_ui_parameters={"persistAuthorization": True},  # keeps token after page refresh
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_cache_for_app_ui(request, call_next):
    """Avoid stale HTML/JS when the UI is served from the same FastAPI app."""
    response = await call_next(request)
    p = request.url.path
    if (
        p in {"/", "/index.html", "/app"}
        or p.startswith("/app/")
        or p.endswith((".js", ".css", ".html"))
    ):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ✅ This adds the lock icon and Bearer token input to Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.fields import router as fields_router
from routes.crop_cycles import router as crop_router
from routes.Regions import router as regions_router
from routes.Satellites import router as satellites_router
from routes.Observations import router as observations_router
from routes.Weather import router as weather_router
from routes.Alerts import router as alerts_router
from routes.Bandvalues import router as band_values_router
from routes.Derived_Metrics import router as derived_metrics_router

app.include_router(auth_router,            prefix="/api/auth",            tags=["Authentication"])
app.include_router(users_router,           prefix="/api/users",           tags=["Users"])
app.include_router(regions_router,         prefix="/api/regions",         tags=["Regions"])
app.include_router(fields_router,          prefix="/api/fields",          tags=["Fields"])
app.include_router(crop_router,            prefix="/api/crop-cycles",     tags=["Crop Cycles"])
app.include_router(satellites_router,      prefix="/api/satellites",      tags=["Satellites"])
app.include_router(observations_router,    prefix="/api/observations",    tags=["Observations"])
app.include_router(weather_router,         prefix="/api/weather",         tags=["Weather"])
app.include_router(alerts_router,          prefix="/api/alerts",          tags=["Alerts"])
app.include_router(band_values_router,     prefix="/api/band-values",     tags=["Band Values"])
app.include_router(derived_metrics_router, prefix="/api/derived-metrics", tags=["Derived Metrics"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])

_frontend = Path(__file__).resolve().parent / "frontend"
_uploads = Path(__file__).resolve().parent / "uploads"
_uploads.mkdir(parents=True, exist_ok=True)
(_uploads / "avatars").mkdir(parents=True, exist_ok=True)

if _frontend.is_dir():
    app.mount("/app", StaticFiles(directory=str(_frontend), html=True), name="frontend")
if _uploads.is_dir():
    app.mount("/media", StaticFiles(directory=str(_uploads)), name="media")
if _frontend.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend_root")


@app.on_event("startup")
def startup_tasks():
    apply_startup_migrations()

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "message": "HarvestHUB API is running", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)