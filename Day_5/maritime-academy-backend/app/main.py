import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine
from app.api.v1.endpoints import auth, users, courses, trips, payments, ai
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Test database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown: Dispose database engine
    engine.dispose()
    logger.info("Database engine disposed")

app = FastAPI(
    title="Maritime Academy API",
    version="1.0.0",
    description="Professional Shipping & Maritime Training Platform",
    lifespan=lifespan
)

# CORS Configuration
allowed_origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Health"])
def root():
    return {"message": "Welcome to Maritime Academy API", "status": "running"}

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1") 
app.include_router(courses.router, prefix="/api/v1")   
app.include_router(trips.router, prefix="/api/v1") 
app.include_router(payments.router, prefix="/api/v1")   
app.include_router(ai.router, prefix="/api/v1")     