import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.document import Document
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.utils.file_utils import save_upload_file, validate_file

router = APIRouter()

@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process research papers"""
    try:
        uploaded_docs = []
        
        for file in files:
            # Validate file
            validation_result = validate_file(file)
            if not validation_result["valid"]:
                raise HTTPException(status_code=400, detail=validation_result["error"])
            
            # Read file content
            content = await file.read()
            
            # Calculate content hash
            content_hash = document_processor.calculate_content_hash(content)
            
            # Check if document already exists
            existing_doc = db.query(Document).filter(Document.content_hash == content_hash).first()
            if existing_doc:
                uploaded_docs.append({
                    "id": existing_doc.id,
                    "filename": existing_doc.filename,
                    "status": "already_exists",
                    "message": "Document already uploaded"
                })
                continue
            
            # Save file
            file_id = str(uuid.uuid4())
            file_path = await save_upload_file(file, content, file_id)
            
            # Create database record
            doc = Document(
                filename=f"{file_id}_{file.filename}",
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=len(content),
                content_hash=content_hash,
                processing_status="pending"
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Schedule background processing
            background_tasks.add_task(process_document_background, doc.id, content, file.filename)
            
            uploaded_docs.append({
                "id": doc.id,
                "filename": doc.original_filename,
                "status": "uploaded",
                "message": "Document uploaded and queued for processing"
            })
        
        return {
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_docs)} document(s)",
            "documents": uploaded_docs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_document_background(doc_id: int, content: bytes, filename: str):
    """Background task to process uploaded document"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get document record
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
        
        # Update status
        doc.processing_status = "processing"
        db.commit()
        
        # Determine file type and process
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.pdf':
            result = await document_processor.process_pdf(content, filename)
        elif file_ext == '.docx':
            result = await document_processor.process_docx(content, filename)
        elif file_ext == '.txt':
            result = await document_processor.process_text(content, filename)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Add to vector store
        await vector_store.add_document(
            document_id=str(doc_id),
            chunks=result['chunks'],
            metadata=result['metadata']
        )
        
        # Update document record
        doc.total_pages = result['metadata'].get('total_pages', 0)
        doc.total_chunks = result['metadata']['total_chunks']
        doc.total_characters = result['metadata']['total_characters']
        doc.is_processed = True
        doc.processing_status = "completed"
        
        db.commit()
        
    except Exception as e:
        # Update error status
        doc.processing_status = "failed"
        doc.error_message = str(e)
        db.commit()
        
    finally:
        db.close()

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    try:
        documents = db.query(Document).order_by(Document.created_at.desc()).all()
        
        return {
            "success": True,
            "documents": [doc.to_dict() for doc in documents],
            "total": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": doc.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from vector store
        await vector_store.remove_document(str(document_id))
        
        # Delete file
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete database record
        db.delete(doc)
        db.commit()
        
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/{document_id}/status")
async def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document processing status"""
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "status": {
                "processing_status": doc.processing_status,
                "is_processed": doc.is_processed,
                "error_message": doc.error_message,
                "total_chunks": doc.total_chunks,
                "total_characters": doc.total_characters
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document status: {str(e)}")

@router.post("/batch-delete")
async def batch_delete_documents(
    document_ids: List[int],
    db: Session = Depends(get_db)
):
    """Delete multiple documents"""
    try:
        deleted_count = 0
        errors = []
        
        for doc_id in document_ids:
            try:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    # Remove from vector store
                    await vector_store.remove_document(str(doc_id))
                    
                    # Delete file
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                    
                    # Delete database record
                    db.delete(doc)
                    deleted_count += 1
                else:
                    errors.append(f"Document {doc_id} not found")
                    
            except Exception as e:
                errors.append(f"Failed to delete document {doc_id}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} document(s)",
            "deleted_count": deleted_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")