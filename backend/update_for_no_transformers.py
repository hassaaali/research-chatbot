#!/usr/bin/env python3
"""
Update backend code to work without transformers/tokenizers
"""
import os
from pathlib import Path

def update_embedding_service():
    """Update embedding service to work without sentence-transformers"""
    service_path = Path("app/services/embedding_service.py")
    
    if not service_path.exists():
        print("[ERROR] embedding_service.py not found")
        return
    
    # Create alternative implementation
    alternative_code = '''import asyncio
import numpy as np
from typing import List, Union, Dict, Any
from loguru import logger
import hashlib

from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = "simple_embeddings"
        self.dimension = 384  # Standard dimension
        self.is_initialized = False
        self.use_simple_embeddings = True
    
    async def initialize(self):
        """Initialize the embedding service"""
        if self.is_initialized:
            return
        
        try:
            # Try to import sentence-transformers
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                SentenceTransformer, 
                settings.EMBEDDING_MODEL
            )
            self.use_simple_embeddings = False
            logger.info("✅ Sentence transformers loaded successfully")
            
        except ImportError:
            logger.warning("Sentence transformers not available, using simple embeddings")
            self.use_simple_embeddings = True
        except Exception as e:
            logger.warning(f"Failed to load sentence transformers: {e}, using simple embeddings")
            self.use_simple_embeddings = True
        
        self.is_initialized = True
        logger.info(f"✅ Embedding service initialized (simple: {self.use_simple_embeddings})")
    
    async def encode_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.use_simple_embeddings:
                return self._simple_embedding(text)
            else:
                # Use sentence transformers
                cleaned_text = self._preprocess_text(text)
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    self.model.encode,
                    cleaned_text
                )
                return embedding
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Fallback to simple embedding
            return self._simple_embedding(text)
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.use_simple_embeddings:
                return [self._simple_embedding(text) for text in texts]
            else:
                # Use sentence transformers
                cleaned_texts = [self._preprocess_text(text) for text in texts]
                embeddings = []
                
                for i in range(0, len(cleaned_texts), batch_size):
                    batch = cleaned_texts[i:i + batch_size]
                    loop = asyncio.get_event_loop()
                    batch_embeddings = await loop.run_in_executor(
                        None,
                        self.model.encode,
                        batch
                    )
                    embeddings.extend(batch_embeddings)
                
                return embeddings
                
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Fallback to simple embeddings
            return [self._simple_embedding(text) for text in texts]
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """Generate a simple hash-based embedding"""
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Create multiple hash-based features
        features = []
        
        # Word-based features
        words = text.lower().split()
        word_hashes = [hash(word) % 1000 for word in words[:50]]  # Limit to 50 words
        word_features = np.zeros(100)
        for h in word_hashes:
            word_features[h % 100] += 1
        features.extend(word_features)
        
        # Character n-gram features
        for n in [2, 3, 4]:
            ngrams = [text[i:i+n] for i in range(len(text)-n+1)]
            ngram_hashes = [hash(ngram) % 1000 for ngram in ngrams[:50]]
            ngram_features = np.zeros(50)
            for h in ngram_hashes:
                ngram_features[h % 50] += 1
            features.extend(ngram_features)
        
        # Text statistics
        stats = [
            len(text),
            len(words),
            len(set(words)),  # unique words
            sum(len(word) for word in words) / max(len(words), 1),  # avg word length
            text.count('.'),
            text.count('?'),
            text.count('!'),
            text.count(',')
        ]
        features.extend(stats)
        
        # Pad or truncate to desired dimension
        features = np.array(features[:self.dimension])
        if len(features) < self.dimension:
            features = np.pad(features, (0, self.dimension - len(features)))
        
        # Normalize
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features.astype('float32')
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation"""
        if not text or not isinstance(text, str):
            return ""
        
        # Basic cleaning
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Truncate to reasonable length
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
            "use_simple_embeddings": self.use_simple_embeddings,
            "is_initialized": self.is_initialized
        }

# Global instance
embedding_service = EmbeddingService()
'''
    
    # Backup original file
    backup_path = service_path.with_suffix('.py.backup')
    if service_path.exists() and not backup_path.exists():
        service_path.rename(backup_path)
        print(f"[SUCCESS] Backed up original embedding_service.py")
    
    # Write new implementation
    with open(service_path, 'w') as f:
        f.write(alternative_code)
    
    print("[SUCCESS] Updated embedding_service.py to work without transformers")

def update_llm_service():
    """Update LLM service to work without transformers"""
    service_path = Path("app/services/llm_service.py")
    
    if not service_path.exists():
        print("[ERROR] llm_service.py not found")
        return
    
    # Create simple implementation
    simple_code = '''import asyncio
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.config import settings

class LLMService:
    def __init__(self):
        self.model = None
        self.model_name = "simple_response_generator"
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the LLM service"""
        if self.is_initialized:
            return
        
        try:
            # Try to import transformers
            from transformers import pipeline
            
            logger.info("Loading simple text generation model...")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                pipeline,
                "text-generation",
                "gpt2"
            )
            logger.info("✅ Transformers model loaded")
            
        except ImportError:
            logger.warning("Transformers not available, using simple response generation")
            self.model = None
        except Exception as e:
            logger.warning(f"Failed to load transformers: {e}, using simple response generation")
            self.model = None
        
        self.is_initialized = True
        logger.info("✅ LLM service initialized")
    
    async def generate_response(self, query: str, context: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using simple logic or transformers if available"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.model:
                return await self._generate_with_transformers(query, context, options)
            else:
                return await self._generate_simple_response(query, context, options)
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return await self._generate_fallback_response(query, context)
    
    async def _generate_with_transformers(self, query: str, context: List[Dict[str, Any]], options: Dict[str, Any] = None):
        """Generate response using transformers"""
        options = options or {}
        max_tokens = options.get('max_tokens', 200)
        
        # Build simple prompt
        prompt = f"Question: {query}\\n\\nBased on the research papers:\\n"
        for i, item in enumerate(context[:3], 1):
            text = item.get('text', '')[:200]
            prompt += f"{i}. {text}\\n"
        prompt += "\\nAnswer:"
        
        # Generate response
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.model,
            prompt,
            {"max_new_tokens": max_tokens, "do_sample": True, "temperature": 0.7}
        )
        
        response = result[0]['generated_text'].replace(prompt, "").strip()
        
        return {
            'response': response,
            'model': 'gpt2',
            'tokens_used': len(response.split()),
            'context_used': len(context)
        }
    
    async def _generate_simple_response(self, query: str, context: List[Dict[str, Any]], options: Dict[str, Any] = None):
        """Generate response using simple template-based logic"""
        if not context:
            return {
                'response': "I don't have enough information in the uploaded documents to answer your question. Please make sure you've uploaded relevant research papers.",
                'model': 'simple_template',
                'tokens_used': 0,
                'context_used': 0
            }
        
        # Analyze query type
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'define', 'definition']):
            response = self._generate_definition_response(context)
        elif any(word in query_lower for word in ['compare', 'difference', 'versus']):
            response = self._generate_comparison_response(context)
        elif any(word in query_lower for word in ['summarize', 'summary', 'overview']):
            response = self._generate_summary_response(context)
        elif any(word in query_lower for word in ['method', 'approach', 'how']):
            response = self._generate_methodology_response(context)
        else:
            response = self._generate_general_response(context)
        
        return {
            'response': response,
            'model': 'simple_template',
            'tokens_used': len(response.split()),
            'context_used': len(context)
        }
    
    def _generate_definition_response(self, context: List[Dict[str, Any]]) -> str:
        """Generate definition response"""
        response = "Based on the research papers, here's what I found:\\n\\n"
        
        for i, item in enumerate(context[:3], 1):
            text = item.get('text', '')[:300]
            doc_id = item.get('document_id', 'Unknown')
            response += f"From document {doc_id}: {text}... [{i}]\\n\\n"
        
        return response
    
    def _generate_comparison_response(self, context: List[Dict[str, Any]]) -> str:
        """Generate comparison response"""
        response = "Here's a comparison based on the research papers:\\n\\n"
        
        for i, item in enumerate(context[:3], 1):
            text = item.get('text', '')[:250]
            doc_id = item.get('document_id', 'Unknown')
            response += f"**Document {doc_id}:** {text}... [{i}]\\n\\n"
        
        return response
    
    def _generate_summary_response(self, context: List[Dict[str, Any]]) -> str:
        """Generate summary response"""
        response = "Here's a summary of the key findings:\\n\\n"
        
        for i, item in enumerate(context[:4], 1):
            text = item.get('text', '')[:200]
            response += f"• {text}... [{i}]\\n\\n"
        
        return response
    
    def _generate_methodology_response(self, context: List[Dict[str, Any]]) -> str:
        """Generate methodology response"""
        response = "Here are the methodologies and approaches mentioned:\\n\\n"
        
        for i, item in enumerate(context[:3], 1):
            text = item.get('text', '')[:300]
            doc_id = item.get('document_id', 'Unknown')
            response += f"**From document {doc_id}:** {text}... [{i}]\\n\\n"
        
        return response
    
    def _generate_general_response(self, context: List[Dict[str, Any]]) -> str:
        """Generate general response"""
        response = "Based on your research papers, here's what I found:\\n\\n"
        
        for i, item in enumerate(context[:4], 1):
            text = item.get('text', '')[:250]
            doc_id = item.get('document_id', 'Unknown')
            response += f"{text}... [Source: Document {doc_id}]\\n\\n"
        
        return response
    
    async def _generate_fallback_response(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback response when everything fails"""
        if not context:
            response = "I don't have enough information to answer your question. Please upload relevant research papers."
        else:
            response = "I found some relevant information in your documents, but I'm having trouble generating a detailed response. Here are the key excerpts:\\n\\n"
            for i, item in enumerate(context[:2], 1):
                text = item.get('text', '')[:200]
                response += f"{i}. {text}...\\n\\n"
        
        return {
            'response': response,
            'model': 'fallback',
            'tokens_used': 0,
            'context_used': len(context),
            'error': 'Response generation failed'
        }
    
    async def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify the type of query"""
        try:
            query_lower = query.lower()
            
            categories = {
                'definition': ['what is', 'define', 'definition', 'meaning', 'explain'],
                'comparison': ['compare', 'difference', 'versus', 'vs', 'similar', 'different'],
                'summary': ['summarize', 'summary', 'overview', 'main points', 'key findings'],
                'methodology': ['methodology', 'method', 'approach', 'procedure', 'how'],
                'results': ['results', 'findings', 'outcomes', 'conclusions'],
                'analysis': ['analyze', 'analysis', 'evaluate', 'assessment']
            }
            
            scores = {}
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > 0:
                    scores[category] = score / len(keywords)
            
            if scores:
                best_category = max(scores, key=scores.get)
                confidence = scores[best_category]
            else:
                best_category = 'general'
                confidence = 0.5
            
            return {
                'category': best_category,
                'confidence': confidence,
                'all_scores': scores
            }
            
        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            return {
                'category': 'general',
                'confidence': 0.5,
                'all_scores': {}
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'is_initialized': self.is_initialized,
            'has_transformers': self.model is not None,
            'model_type': type(self.model).__name__ if self.model else 'simple_template'
        }

# Global instance
llm_service = LLMService()
'''
    
    # Backup original file
    backup_path = service_path.with_suffix('.py.backup')
    if service_path.exists() and not backup_path.exists():
        service_path.rename(backup_path)
        print(f"[SUCCESS] Backed up original llm_service.py")
    
    # Write new implementation
    with open(service_path, 'w') as f:
        f.write(simple_code)
    
    print("[SUCCESS] Updated llm_service.py to work without transformers")

def create_simple_env():
    """Create environment configuration for simple mode"""
    env_content = '''# Simple configuration without Rust-dependent packages
ENABLE_ADVANCED_NLP=False
USE_SIMPLE_EMBEDDINGS=True
TEXT_GENERATION_MODEL=""
EMBEDDING_MODEL=""

# Vector store
VECTOR_STORE_TYPE=chromadb

# Web search (still works)
ENABLE_WEB_SEARCH=True
SEARCH_ENGINE=duckduckgo

# Basic settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.3
'''
    
    with open(".env.simple", 'w') as f:
        f.write(env_content)
    
    print("[SUCCESS] Created .env.simple with basic configuration")

def main():
    print("Updating Backend for No Transformers/Tokenizers")
    print("=" * 50)
    
    # Update services
    update_embedding_service()
    update_llm_service()
    
    # Create simple environment
    create_simple_env()
    
    print("\n[SUCCESS] Backend updated for simple mode!")
    print("\n[INFO] Changes made:")
    print("   ✅ Embedding service uses simple hash-based embeddings")
    print("   ✅ LLM service uses template-based responses")
    print("   ✅ Created .env.simple with basic configuration")
    
    print("\n[INFO] Next steps:")
    print("1. Copy settings from .env.simple to your .env file")
    print("2. Run: python main.py")
    print("3. The system will work with basic functionality")
    
    print("\n[INFO] Functionality available:")
    print("   ✅ Document upload and processing")
    print("   ✅ Basic text search")
    print("   ✅ Template-based responses")
    print("   ✅ Web search integration")
    print("   ✅ Chat interface")

if __name__ == "__main__":
    main()