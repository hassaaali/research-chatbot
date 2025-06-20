import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import ChatSession, ChatMessage
from app.services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    include_web_search: bool = True
    max_tokens: int = 512
    temperature: float = 0.7

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: dict
    metadata: dict

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest, db: Session = Depends(get_db)):
    """Process a chat query using RAG"""
    try:
        # Create or get session
        session_id = request.session_id or str(uuid.uuid4())
        
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id)
            db.add(session)
            db.commit()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            message_type="user",
            content=request.message
        )
        db.add(user_message)
        
        # Process query with RAG
        rag_response = await rag_service.query(
            question=request.message,
            document_ids=request.document_ids,
            options={
                'include_web_search': request.include_web_search,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature
            }
        )
        
        # Save assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            message_type="assistant",
            content=rag_response['answer'],
            retrieved_chunks=str(rag_response['sources']['documents']),
            web_search_results=str(rag_response['sources']['web']),
            model_used=rag_response['metadata'].get('model_used'),
            tokens_used=rag_response['metadata'].get('tokens_used', 0),
            response_time=0.0  # TODO: Add timing
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            answer=rag_response['answer'],
            session_id=session_id,
            sources=rag_response['sources'],
            metadata=rag_response['metadata']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat query failed: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "type": msg.message_type,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "metadata": {
                    "model_used": msg.model_used,
                    "tokens_used": msg.tokens_used,
                    "response_time": msg.response_time
                } if msg.message_type == "assistant" else None
            })
        
        return {
            "success": True,
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@router.get("/sessions")
async def list_chat_sessions(db: Session = Depends(get_db)):
    """List all chat sessions"""
    try:
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
        
        session_list = []
        for session in sessions:
            # Get message count
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).count()
            
            # Get last message
            last_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            session_list.append({
                "session_id": session.session_id,
                "title": session.title or f"Chat {session.session_id[:8]}",
                "message_count": message_count,
                "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            })
        
        return {
            "success": True,
            "sessions": session_list,
            "total": len(session_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and its messages"""
    try:
        # Delete messages
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # Delete session
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            db.delete(session)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Chat session deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")

@router.post("/similar-questions")
async def get_similar_questions(request: dict):
    """Get similar questions based on current query"""
    try:
        question = request.get('question', '')
        document_ids = request.get('document_ids')
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        similar_questions = await rag_service.get_similar_questions(
            question=question,
            document_ids=document_ids
        )
        
        return {
            "success": True,
            "similar_questions": similar_questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get similar questions: {str(e)}")

@router.post("/summarize")
async def summarize_documents(request: dict):
    """Generate a summary of specified documents"""
    try:
        document_ids = request.get('document_ids', [])
        
        if not document_ids:
            raise HTTPException(status_code=400, detail="Document IDs are required")
        
        summary = await rag_service.summarize_documents(document_ids)
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize documents: {str(e)}")