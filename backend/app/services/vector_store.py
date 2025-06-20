import os
import json
import pickle
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from loguru import logger

from app.core.config import settings
from app.services.embedding_service import embedding_service

class VectorStore:
    def __init__(self):
        self.index = None
        self.metadata = {}
        self.document_chunks = {}
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.metadata_path = self.index_path / "metadata.json"
        self.chunks_path = self.index_path / "chunks.pkl"
        self.dimension = settings.EMBEDDING_DIMENSION
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the vector store"""
        if self.is_initialized:
            return
        
        try:
            # Create directory if it doesn't exist
            self.index_path.mkdir(parents=True, exist_ok=True)
            
            # Load existing index or create new one
            await self._load_or_create_index()
            
            self.is_initialized = True
            logger.info(f"✅ Vector store initialized with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise
    
    async def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        index_file = self.index_path / "index.faiss"
        
        if index_file.exists():
            try:
                # Load existing index
                self.index = faiss.read_index(str(index_file))
                
                # Load metadata
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'r') as f:
                        self.metadata = json.load(f)
                
                # Load chunks
                if self.chunks_path.exists():
                    with open(self.chunks_path, 'rb') as f:
                        self.document_chunks = pickle.load(f)
                
                logger.info(f"Loaded existing vector store with {self.index.ntotal} vectors")
                
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Creating new one.")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Create a flat L2 index for exact search
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        self.document_chunks = {}
        logger.info("Created new FAISS index")
    
    async def add_document(self, document_id: str, chunks: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add document chunks to the vector store"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"Adding document {document_id} with {len(chunks)} chunks to vector store")
            
            # Extract text from chunks
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await embedding_service.encode_batch(texts)
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Get current index size for ID mapping
            start_id = self.index.ntotal
            
            # Add to FAISS index
            self.index.add(embeddings_array)
            
            # Store metadata and chunks
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = start_id + i
                
                # Store metadata
                self.metadata[str(vector_id)] = {
                    'document_id': document_id,
                    'chunk_index': chunk['index'],
                    'chunk_size': chunk['size'],
                    'start_pos': chunk.get('start_pos', 0),
                    **(metadata or {})
                }
                
                # Store chunk data
                if document_id not in self.document_chunks:
                    self.document_chunks[document_id] = {}
                
                self.document_chunks[document_id][chunk['index']] = {
                    'text': chunk['text'],
                    'vector_id': vector_id,
                    'embedding': embedding.tolist()  # Store as list for JSON serialization
                }
            
            # Save to disk
            await self._save_index()
            
            result = {
                'document_id': document_id,
                'chunks_added': len(chunks),
                'total_vectors': self.index.ntotal,
                'vector_ids': list(range(start_id, start_id + len(chunks)))
            }
            
            logger.info(f"Successfully added {len(chunks)} chunks for document {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to vector store: {e}")
            raise
    
    async def search(self, query: str, top_k: int = 10, document_ids: Optional[List[str]] = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if self.index.ntotal == 0:
                return []
            
            # Generate query embedding
            query_embedding = await embedding_service.encode_text(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # Search in FAISS index
            # Use larger k for filtering if document_ids specified
            search_k = min(top_k * 3 if document_ids else top_k, self.index.ntotal)
            distances, indices = self.index.search(query_vector, search_k)
            
            results = []
            similarity_threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD
            
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + distance)
                
                if similarity < similarity_threshold:
                    continue
                
                # Get metadata
                vector_metadata = self.metadata.get(str(idx), {})
                document_id = vector_metadata.get('document_id')
                
                # Filter by document IDs if specified
                if document_ids and document_id not in document_ids:
                    continue
                
                # Get chunk data
                chunk_index = vector_metadata.get('chunk_index', 0)
                chunk_data = self.document_chunks.get(document_id, {}).get(chunk_index, {})
                
                result = {
                    'vector_id': int(idx),
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'text': chunk_data.get('text', ''),
                    'similarity': float(similarity),
                    'distance': float(distance),
                    'metadata': vector_metadata
                }
                
                results.append(result)
                
                # Stop if we have enough results
                if len(results) >= top_k:
                    break
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []
    
    async def remove_document(self, document_id: str) -> Dict[str, Any]:
        """Remove all chunks for a document"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Find vector IDs to remove
            vector_ids_to_remove = []
            for vector_id, metadata in self.metadata.items():
                if metadata.get('document_id') == document_id:
                    vector_ids_to_remove.append(int(vector_id))
            
            if not vector_ids_to_remove:
                return {'removed_chunks': 0, 'message': 'Document not found'}
            
            # FAISS doesn't support direct removal, so we need to rebuild the index
            # This is expensive but necessary for now
            await self._rebuild_index_without_vectors(vector_ids_to_remove)
            
            # Remove from metadata and chunks
            for vector_id in vector_ids_to_remove:
                self.metadata.pop(str(vector_id), None)
            
            self.document_chunks.pop(document_id, None)
            
            # Save updated index
            await self._save_index()
            
            result = {
                'document_id': document_id,
                'removed_chunks': len(vector_ids_to_remove),
                'total_vectors': self.index.ntotal
            }
            
            logger.info(f"Removed {len(vector_ids_to_remove)} chunks for document {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove document {document_id}: {e}")
            raise
    
    async def _rebuild_index_without_vectors(self, vector_ids_to_remove: List[int]):
        """Rebuild FAISS index without specified vectors"""
        if not vector_ids_to_remove:
            return
        
        # Get all current vectors
        all_vectors = []
        valid_metadata = {}
        valid_chunks = {}
        
        for i in range(self.index.ntotal):
            if i not in vector_ids_to_remove:
                # Reconstruct vector from index
                vector = self.index.reconstruct(i)
                all_vectors.append(vector)
                
                # Keep metadata with new ID
                new_id = len(all_vectors) - 1
                if str(i) in self.metadata:
                    old_metadata = self.metadata[str(i)]
                    valid_metadata[str(new_id)] = old_metadata
                    
                    # Update chunks with new vector ID
                    doc_id = old_metadata.get('document_id')
                    chunk_idx = old_metadata.get('chunk_index')
                    
                    if doc_id and doc_id in self.document_chunks and chunk_idx in self.document_chunks[doc_id]:
                        if doc_id not in valid_chunks:
                            valid_chunks[doc_id] = {}
                        valid_chunks[doc_id][chunk_idx] = self.document_chunks[doc_id][chunk_idx]
                        valid_chunks[doc_id][chunk_idx]['vector_id'] = new_id
        
        # Create new index
        self._create_new_index()
        
        if all_vectors:
            # Add all valid vectors to new index
            vectors_array = np.array(all_vectors).astype('float32')
            self.index.add(vectors_array)
        
        # Update metadata and chunks
        self.metadata = valid_metadata
        self.document_chunks = valid_chunks
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            index_file = self.index_path / "index.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            # Save chunks
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.document_chunks, f)
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if not self.is_initialized:
            await self.initialize()
        
        # Count documents
        document_ids = set()
        for metadata in self.metadata.values():
            if 'document_id' in metadata:
                document_ids.add(metadata['document_id'])
        
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'total_documents': len(document_ids),
            'dimension': self.dimension,
            'index_type': type(self.index).__name__ if self.index else None,
            'is_initialized': self.is_initialized
        }

# Global instance
vector_store = VectorStore()