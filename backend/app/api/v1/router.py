from fastapi import APIRouter

from .core.endpoints import router as core_router
from .data.endpoints import router as data_router
from .models.endpoints import router as models_router
from .predictions.endpoints import router as predictions_router
from .quiniela.endpoints import router as quiniela_router
from .analytics.endpoints import router as analytics_router
from .advanced.endpoints import router as advanced_router

# Create the main v1 API router
api_v1_router = APIRouter()

# Include all domain routers with their prefixes
api_v1_router.include_router(core_router, tags=["core"])
api_v1_router.include_router(data_router, prefix="/data", tags=["data"])
api_v1_router.include_router(models_router, prefix="/model", tags=["models"])
api_v1_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
api_v1_router.include_router(quiniela_router, prefix="/quiniela", tags=["quiniela"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_v1_router.include_router(advanced_router, prefix="/advanced-data", tags=["advanced"])