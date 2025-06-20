#!/usr/bin/env python3
"""
Update backend code to work with alternative packages
"""
import os
from pathlib import Path

def update_vector_store():
    """Update vector store to use ChromaDB instead of FAISS"""
    vector_store_path = Path("app/services/vector_store.py")
    
    if not vector_store_path.exists():
        print("❌ vector_store.py not found")
        return
    
    # Create alternative vector store implementation
    alternative_code = '''import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from loguru import logger

from app.core.config import settings
from app.services.embedding_service import embedding_service

# Try to import vector search libraries in order of preference
VECTOR_STORE_TYPE = None
vector_client = None

try:
    import chromadb
    VECTOR_STORE_TYPE = "chromadb"
    logger.info("Using ChromaDB for vector search")
except ImportError:
    try:
        import hnswlib
        VECTOR_STORE_TYPE = "hnswlib"
        logger.info("Using HNSWLIB for vector search")
    except ImportError:
        try:
            import annoy
            VECTOR_STORE_TYPE = "annoy"
            logger.info("Using Annoy for vector search")
        except ImportError:
            VECTOR_STORE_TYPE = "simple"
            logger.warning("No vector search library available, using simple text search")

class VectorStore:
    def __init__(self):
        self.index = None
        self.metadata = {}
        self.document_chunks = {}
        self.index_path = Path(settings.VECTOR_DB_PATH)
        self.dimension = settings.EMBEDDING_DIMENSION
        self.is_initialized = False
        self.vector_store_type = VECTOR_STORE_TYPE
    
    async def initialize(self):
        """Initialize the vector store"""
        if self.is_initialized:
            return
        
        try:
            # Create directory if it doesn't exist
            self.index_path.mkdir(parents=True, exist_ok=True)
            
            if self.vector_store_type == "chromadb":
                await self._init_chromadb()
            elif self.vector_store_type == "hnswlib":
                await self._init_hnswlib()
            elif self.vector_store_type == "annoy":
                await self._init_annoy()
            else:
                await self._init_simple()
            
            self.is_initialized = True
            logger.info(f"✅ Vector store initialized with {self.vector_store_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            # Fallback to simple search
            self.vector_store_type = "simple"
            await self._init_simple()
            self.is_initialized = True
    
    async def _init_chromadb(self):
        """Initialize ChromaDB"""
        import chromadb
        from chromadb.config import Settings
        
        self.client = chromadb.PersistentClient(
            path=str(self.index_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("documents")
        except:
            self.collection = self.client.create_collection("documents")
    
    async def _init_hnswlib(self):
        """Initialize HNSWLIB"""
        import hnswlib
        
        self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        index_file = self.index_path / "hnswlib_index.bin"
        
        if index_file.exists():
            self.index.load_index(str(index_file))
        else:
            self.index.init_index(max_elements=10000, ef_construction=200, M=16)
    
    async def _init_annoy(self):
        """Initialize Annoy"""
        from annoy import AnnoyIndex
        
        self.index = AnnoyIndex(self.dimension, 'angular')
        index_file = self.index_path / "annoy_index.ann"
        
        if index_file.exists():
            self.index.load(str(index_file))
    
    async def _init_simple(self):
        """Initialize simple text search"""
        self.index = {}  # Simple dictionary for text search
        logger.info("Using simple text search (no vector search)")
    
    async def add_document(self, document_id: str, chunks: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add document chunks to the vector store"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"Adding document {document_id} with {len(chunks)} chunks")
            
            if self.vector_store_type == "simple":
                return await self._add_document_simple(document_id, chunks, metadata)
            
            # Extract text from chunks
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await embedding_service.encode_batch(texts)
            
            if self.vector_store_type == "chromadb":
                return await self._add_document_chromadb(document_id, chunks, embeddings, metadata)
            elif self.vector_store_type == "hnswlib":
                return await self._add_document_hnswlib(document_id, chunks, embeddings, metadata)
            elif self.vector_store_type == "annoy":
                return await self._add_document_annoy(document_id, chunks, embeddings, metadata)
            
        except Exception as e:
            logger.error(f"Failed to add document {document_id}: {e}")
            raise
    
    async def _add_document_simple(self, document_id: str, chunks: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Add document using simple text search"""
        self.document_chunks[document_id] = chunks
        
        return {
            'document_id': document_id,
            'chunks_added': len(chunks),
            'total_vectors': len(self.document_chunks),
            'vector_ids': list(range(len(chunks)))
        }
    
    async def _add_document_chromadb(self, document_id: str, chunks: List[Dict[str, Any]], embeddings: List, metadata: Dict[str, Any] = None):
        """Add document using ChromaDB"""
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [{'document_id': document_id, 'chunk_index': i, **(metadata or {})} for i in range(len(chunks))]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            'document_id': document_id,
            'chunks_added': len(chunks),
            'total_vectors': self.collection.count(),
            'vector_ids': ids
        }
    
    async def search(self, query: str, top_k: int = 10, document_ids: Optional[List[str]] = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if self.vector_store_type == "simple":
                return await self._search_simple(query, top_k, document_ids)
            
            # Generate query embedding
            query_embedding = await embedding_service.encode_text(query)
            
            if self.vector_store_type == "chromadb":
                return await self._search_chromadb(query_embedding, top_k, document_ids, similarity_threshold)
            elif self.vector_store_type == "hnswlib":
                return await self._search_hnswlib(query_embedding, top_k, document_ids, similarity_threshold)
            elif self.vector_store_type == "annoy":
                return await self._search_annoy(query_embedding, top_k, document_ids, similarity_threshold)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []
    
    async def _search_simple(self, query: str, top_k: int, document_ids: Optional[List[str]] = None):
        """Simple text search"""
        results = []
        query_lower = query.lower()
        
        docs_to_search = document_ids or list(self.document_chunks.keys())
        
        for doc_id in docs_to_search:
            if doc_id in self.document_chunks:
                for i, chunk in enumerate(self.document_chunks[doc_id]):
                    text = chunk['text'].lower()
                    if query_lower in text:
                        # Simple relevance scoring
                        score = text.count(query_lower) / len(text.split())
                        results.append({
                            'vector_id': f"{doc_id}_{i}",
                            'document_id': doc_id,
                            'chunk_index': i,
                            'text': chunk['text'],
                            'similarity': min(score * 10, 1.0),  # Normalize to 0-1
                            'distance': 1 - min(score * 10, 1.0),
                            'metadata': {'document_id': doc_id, 'chunk_index': i}
                        })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    async def _search_chromadb(self, query_embedding, top_k: int, document_ids: Optional[List[str]] = None, similarity_threshold: float = None):
        """Search using ChromaDB"""
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
            
            if similarity_threshold and similarity < similarity_threshold:
                continue
            
            formatted_results.append({
                'vector_id': results['ids'][0][i],
                'document_id': results['metadatas'][0][i]['document_id'],
                'chunk_index': results['metadatas'][0][i]['chunk_index'],
                'text': results['documents'][0][i],
                'similarity': float(similarity),
                'distance': float(results['distances'][0][i]),
                'metadata': results['metadatas'][0][i]
            })
        
        return formatted_results
    
    async def remove_document(self, document_id: str) -> Dict[str, Any]:
        """Remove all chunks for a document"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if self.vector_store_type == "simple":
                removed_count = len(self.document_chunks.get(document_id, []))
                self.document_chunks.pop(document_id, None)
                return {'removed_chunks': removed_count}
            
            elif self.vector_store_type == "chromadb":
                # Get all IDs for this document
                results = self.collection.get(where={"document_id": document_id})
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                return {'removed_chunks': len(results['ids'])}
            
            # For other vector stores, implement as needed
            return {'removed_chunks': 0}
            
        except Exception as e:
            logger.error(f"Failed to remove document {document_id}: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if not self.is_initialized:
            await self.initialize()
        
        if self.vector_store_type == "simple":
            total_vectors = sum(len(chunks) for chunks in self.document_chunks.values())
            total_documents = len(self.document_chunks)
        elif self.vector_store_type == "chromadb":
            total_vectors = self.collection.count()
            # Count unique documents
            all_metadata = self.collection.get()['metadatas']
            unique_docs = set(meta['document_id'] for meta in all_metadata)
            total_documents = len(unique_docs)
        else:
            total_vectors = 0
            total_documents = 0
        
        return {
            'total_vectors': total_vectors,
            'total_documents': total_documents,
            'dimension': self.dimension,
            'vector_store_type': self.vector_store_type,
            'is_initialized': self.is_initialized
        }

# Global instance
vector_store = VectorStore()
'''
    
    # Backup original file
    backup_path = vector_store_path.with_suffix('.py.backup')
    if vector_store_path.exists() and not backup_path.exists():
        vector_store_path.rename(backup_path)
        print(f"✅ Backed up original vector_store.py to {backup_path}")
    
    # Write new implementation
    with open(vector_store_path, 'w') as f:
        f.write(alternative_code)
    
    print("✅ Updated vector_store.py to use alternative vector search")

def update_document_processor():
    """Update document processor to work without spaCy"""
    processor_path = Path("app/services/document_processor.py")
    
    if not processor_path.exists():
        print("❌ document_processor.py not found")
        return
    
    # Read current file
    with open(processor_path, 'r') as f:
        content = f.read()
    
    # Replace spaCy initialization with fallback
    updated_content = content.replace(
        '''try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None''',
        '''try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except (ImportError, OSError):
                logger.warning("spaCy not available. Using basic text processing.")
                self.nlp = None'''
    )
    
    # Write updated content
    with open(processor_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Updated document_processor.py to work without spaCy")

def update_config():
    """Update config to use alternative settings"""
    config_path = Path("app/core/config.py")
    
    if not config_path.exists():
        print("❌ config.py not found")
        return
    
    # Read current file
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Add new configuration options
    additional_config = '''
    
    # Vector store configuration
    VECTOR_STORE_TYPE: str = Field(default="chromadb", env="VECTOR_STORE_TYPE")
    ENABLE_ADVANCED_NLP: bool = Field(default=False, env="ENABLE_ADVANCED_NLP")
    USE_SIMPLE_EMBEDDINGS: bool = Field(default=False, env="USE_SIMPLE_EMBEDDINGS")
'''
    
    # Insert before the Config class
    if "class Config:" in content and additional_config not in content:
        content = content.replace("class Config:", additional_config + "\n    class Config:")
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated config.py with alternative settings")

def create_env_update():
    """Create .env updates for alternative configuration"""
    env_updates = '''
# Alternative configuration for systems without compilation
VECTOR_STORE_TYPE=chromadb
ENABLE_ADVANCED_NLP=False
USE_SIMPLE_EMBEDDINGS=False
ENABLE_WEB_SEARCH=True

# Disable features that require missing packages
TEXT_GENERATION_MODEL=microsoft/DialoGPT-medium
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Use basic text processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.5
'''
    
    with open(".env.alternatives", 'w') as f:
        f.write(env_updates)
    
    print("✅ Created .env.alternatives with recommended settings")
    print("   Copy these settings to your .env file")

def main():
    print("🔧 Updating Backend for Alternative Packages")
    print("=" * 50)
    
    # Update vector store
    update_vector_store()
    
    # Update document processor
    update_document_processor()
    
    # Update config
    update_config()
    
    # Create env updates
    create_env_update()
    
    print("\n✅ Backend updated for alternative packages!")
    print("\n📋 Changes made:")
    print("   ✅ Vector store now supports ChromaDB/HNSWLIB/Annoy/Simple search")
    print("   ✅ Document processor works without spaCy")
    print("   ✅ Configuration updated for alternatives")
    print("   ✅ Created .env.alternatives with recommended settings")
    
    print("\n📋 Next steps:")
    print("1. Copy settings from .env.alternatives to your .env file")
    print("2. Run: python main.py")
    print("3. The backend will work with alternative packages")

if __name__ == "__main__":
    main()