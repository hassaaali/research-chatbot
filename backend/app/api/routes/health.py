from fastapi import APIRouter
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "message": "Research Paper RAG Backend is running"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    try:
        # Check vector store
        vector_stats = await vector_store.get_stats()
        
        # Check embedding service
        embedding_info = await embedding_service.get_model_info()
        
        # Check LLM service
        llm_info = await llm_service.get_model_info()
        
        return {
            "status": "healthy",
            "services": {
                "vector_store": {
                    "status": "healthy" if vector_stats["is_initialized"] else "unhealthy",
                    "stats": vector_stats
                },
                "embedding_service": {
                    "status": "healthy" if embedding_info["is_initialized"] else "unhealthy",
                    "info": embedding_info
                },
                "llm_service": {
                    "status": "healthy" if llm_info["is_initialized"] else "unhealthy",
                    "info": llm_info
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }