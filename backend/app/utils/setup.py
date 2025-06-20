import os
import asyncio
from pathlib import Path
from loguru import logger

from app.core.config import settings

async def create_directories():
    """Create necessary directories"""
    directories = [
        settings.VECTOR_DB_PATH,
        settings.FAISS_INDEX_PATH,
        settings.DOCUMENTS_PATH,
        settings.UPLOAD_PATH,
        "./logs",
        "./data"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {directory}: {e}")
            raise

async def download_models():
    """Download required models"""
    try:
        logger.info("📥 Downloading required models...")
        
        # Download spaCy model if not present
        try:
            import spacy
            spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model already available")
        except OSError:
            logger.info("📥 Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            logger.info("✅ spaCy model downloaded")
        
        # Download NLTK data
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        logger.info("✅ NLTK data downloaded")
        
        logger.info("✅ All models downloaded successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Model download failed: {e}")
        # Don't raise error as models can be downloaded on-demand