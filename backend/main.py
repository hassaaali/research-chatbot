import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import documents, chat, health
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.utils.setup import create_directories, download_models

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Research Paper RAG Backend")
    
    try:
        # Create necessary directories
        await create_directories()
        
        # Initialize database
        await init_db()
        
        # Download and initialize models
        await download_models()
        
        # Initialize services
        await embedding_service.initialize()
        await vector_store.initialize()
        
        logger.info("✅ Backend initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Research Paper RAG Backend")

# Create FastAPI app
app = FastAPI(
    title="Research Paper RAG Backend",
    description="Backend API for Research Paper Chat Assistant with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static files
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routes
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Research Paper RAG Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )