from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .api.v1.router import api_v1_router
from .api.endpoints_multiple import router as multiple_router
from .config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quiniela Predictor API",
    description="API for predicting Spanish football quiniela results",
    version="2.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_v1_router)
app.include_router(multiple_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)