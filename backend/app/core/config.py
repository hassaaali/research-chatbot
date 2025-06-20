import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Hugging Face Configuration
    HUGGINGFACE_API_TOKEN: str = Field(default="", env="HUGGINGFACE_API_TOKEN")
    HUGGINGFACE_MODEL: str = Field(
        default="microsoft/DialoGPT-medium", 
        env="HUGGINGFACE_MODEL"
    )
    TEXT_GENERATION_MODEL: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.1",
        env="TEXT_GENERATION_MODEL"
    )
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")
    
    # Storage Paths
    VECTOR_DB_PATH: str = Field(default="./data/vectors", env="VECTOR_DB_PATH")
    FAISS_INDEX_PATH: str = Field(default="./data/faiss_index", env="FAISS_INDEX_PATH")
    DOCUMENTS_PATH: str = Field(default="./data/documents", env="DOCUMENTS_PATH")
    UPLOAD_PATH: str = Field(default="./uploads", env="UPLOAD_PATH")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=50000000, env="MAX_FILE_SIZE")  # 50MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".txt", ".docx"])
    
    # Web Search
    ENABLE_WEB_SEARCH: bool = Field(default=True, env="ENABLE_WEB_SEARCH")
    SEARCH_ENGINE: str = Field(default="duckduckgo", env="SEARCH_ENGINE")
    GOOGLE_API_KEY: str = Field(default="", env="GOOGLE_API_KEY")
    GOOGLE_CSE_ID: str = Field(default="", env="GOOGLE_CSE_ID")
    MAX_SEARCH_RESULTS: int = Field(default=5, env="MAX_SEARCH_RESULTS")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/research_chatbot.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    # RAG Configuration
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    TOP_K_RETRIEVAL: int = Field(default=5, env="TOP_K_RETRIEVAL")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()