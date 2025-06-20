import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.web_search import web_search_service
from app.core.config import settings

class RAGService:
    def __init__(self):
        self.top_k = settings.TOP_K_RETRIEVAL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
    
    async def query(self, question: str, document_ids: Optional[List[str]] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query using RAG pipeline"""
        try:
            options = options or {}
            include_web_search = options.get('include_web_search', True)
            top_k = options.get('top_k', self.top_k)
            
            logger.info(f"Processing RAG query: {question[:100]}...")
            
            # Step 1: Retrieve relevant chunks from vector store
            retrieved_chunks = await vector_store.search(
                query=question,
                top_k=top_k,
                document_ids=document_ids,
                similarity_threshold=self.similarity_threshold
            )
            
            logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks")
            
            # Step 2: Get web search results for additional context (optional)
            web_results = []
            if include_web_search and settings.ENABLE_WEB_SEARCH:
                try:
                    web_results = await web_search_service.search_academic_only(
                        question,
                        num_results=3
                    )
                    logger.info(f"Retrieved {len(web_results)} web search results")
                except Exception as e:
                    logger.warning(f"Web search failed: {e}")
            
            # Step 3: Combine context from documents and web
            context = self._prepare_context(retrieved_chunks, web_results)
            
            # Step 4: Classify query type
            query_classification = await llm_service.classify_query(question)
            
            # Step 5: Generate response using LLM
            llm_response = await llm_service.generate_response(
                query=question,
                context=context,
                options={
                    'max_tokens': options.get('max_tokens', 512),
                    'temperature': options.get('temperature', 0.7)
                }
            )
            
            # Step 6: Prepare final response
            response = {
                'answer': llm_response['response'],
                'sources': {
                    'documents': self._format_document_sources(retrieved_chunks),
                    'web': self._format_web_sources(web_results)
                },
                'metadata': {
                    'query_type': query_classification['category'],
                    'confidence': query_classification['confidence'],
                    'chunks_retrieved': len(retrieved_chunks),
                    'web_results': len(web_results),
                    'model_used': llm_response['model'],
                    'tokens_used': llm_response['tokens_used'],
                    'context_length': len(context)
                }
            }
            
            logger.info("RAG query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question. Please try again.",
                'sources': {'documents': [], 'web': []},
                'metadata': {'error': str(e)},
                'error': True
            }
    
    def _prepare_context(self, retrieved_chunks: List[Dict[str, Any]], web_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare context for LLM from retrieved chunks and web results"""
        context = []
        
        # Add document chunks
        for chunk in retrieved_chunks:
            context.append({
                'text': chunk['text'],
                'source_type': 'document',
                'document_id': chunk['document_id'],
                'similarity': chunk['similarity'],
                'chunk_index': chunk['chunk_index']
            })
        
        # Add web results
        for result in web_results[:2]:  # Limit web results
            context.append({
                'text': result.get('content', result.get('snippet', '')),
                'source_type': 'web',
                'title': result['title'],
                'url': result['url'],
                'relevance_score': result.get('relevance_score', 0.5)
            })
        
        # Sort by relevance/similarity
        context.sort(key=lambda x: x.get('similarity', x.get('relevance_score', 0)), reverse=True)
        
        return context
    
    def _format_document_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format document sources for response"""
        sources = []
        seen_docs = set()
        
        for chunk in chunks:
            doc_id = chunk['document_id']
            if doc_id not in seen_docs:
                sources.append({
                    'document_id': doc_id,
                    'similarity': chunk['similarity'],
                    'chunk_count': sum(1 for c in chunks if c['document_id'] == doc_id),
                    'preview': chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                })
                seen_docs.add(doc_id)
        
        return sources
    
    def _format_web_sources(self, web_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format web sources for response"""
        return [
            {
                'title': result['title'],
                'url': result['url'],
                'snippet': result.get('snippet', ''),
                'relevance_score': result.get('relevance_score', 0.5)
            }
            for result in web_results
        ]
    
    async def get_similar_questions(self, question: str, document_ids: Optional[List[str]] = None) -> List[str]:
        """Generate similar questions based on document content"""
        try:
            # Get some relevant chunks
            chunks = await vector_store.search(
                query=question,
                top_k=3,
                document_ids=document_ids
            )
            
            if not chunks:
                return []
            
            # Generate similar questions based on content
            similar_questions = [
                "What are the main findings discussed in these papers?",
                "Can you summarize the methodology used?",
                "What are the key conclusions?",
                "How do these results compare to other studies?",
                "What are the limitations mentioned?"
            ]
            
            return similar_questions[:3]
            
        except Exception as e:
            logger.error(f"Failed to generate similar questions: {e}")
            return []
    
    async def summarize_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Generate a summary of specified documents"""
        try:
            # Get representative chunks from each document
            all_chunks = []
            for doc_id in document_ids:
                chunks = await vector_store.search(
                    query="summary main findings conclusions",
                    top_k=3,
                    document_ids=[doc_id]
                )
                all_chunks.extend(chunks)
            
            if not all_chunks:
                return {
                    'summary': "No content found in the specified documents.",
                    'document_count': len(document_ids)
                }
            
            # Generate summary using LLM
            summary_query = "Please provide a comprehensive summary of these research papers, highlighting the main findings, methodologies, and conclusions."
            
            context = [
                {
                    'text': chunk['text'],
                    'document_id': chunk['document_id']
                }
                for chunk in all_chunks
            ]
            
            llm_response = await llm_service.generate_response(
                query=summary_query,
                context=context,
                options={'max_tokens': 1024, 'temperature': 0.5}
            )
            
            return {
                'summary': llm_response['response'],
                'document_count': len(document_ids),
                'chunks_analyzed': len(all_chunks),
                'model_used': llm_response['model']
            }
            
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return {
                'summary': "Failed to generate summary due to an error.",
                'error': str(e)
            }

# Global instance
rag_service = RAGService()