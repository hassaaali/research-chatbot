import asyncio
import numpy as np
from typing import List, Union, Dict, Any
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the embedding model"""
        if self.is_initialized:
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            # Load model in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                SentenceTransformer, 
                self.model_name
            )
            
            self.is_initialized = True
            logger.info(f"✅ Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    async def encode_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Clean and prepare text
            cleaned_text = self._preprocess_text(text)
            
            # Generate embedding in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.model.encode,
                cleaned_text
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Clean and prepare texts
            cleaned_texts = [self._preprocess_text(text) for text in texts]
            
            embeddings = []
            
            # Process in batches to manage memory
            for i in range(0, len(cleaned_texts), batch_size):
                batch = cleaned_texts[i:i + batch_size]
                
                # Generate embeddings in executor
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None,
                    self.model.encode,
                    batch
                )
                
                embeddings.extend(batch_embeddings)
                
                # Log progress for large batches
                if len(cleaned_texts) > 50:
                    logger.info(f"Processed {min(i + batch_size, len(cleaned_texts))}/{len(cleaned_texts)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation"""
        if not text or not isinstance(text, str):
            return ""
        
        # Basic cleaning
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Truncate to model's max length (usually 512 tokens)
        # Approximate: 1 token ≈ 4 characters
        max_chars = 2048
        if len(text) > max_chars:
            text = text[:max_chars]
        
        return text
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Ensure result is between -1 and 1
            return float(np.clip(similarity, -1.0, 1.0))
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def calculate_batch_similarity(self, query_embedding: np.ndarray, embeddings: List[np.ndarray]) -> List[float]:
        """Calculate similarities between query and multiple embeddings"""
        try:
            similarities = []
            
            for embedding in embeddings:
                similarity = self.calculate_similarity(query_embedding, embedding)
                similarities.append(similarity)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to calculate batch similarities: {e}")
            return [0.0] * len(embeddings)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if not self.is_initialized:
            await self.initialize()
        
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_seq_length": getattr(self.model, 'max_seq_length', 512),
            "is_initialized": self.is_initialized
        }

# Global instance
embedding_service = EmbeddingService()