from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Quiniela Predictor API", "version": "2.1.0"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}