import os
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO

import PyPDF2
import nltk
import spacy
from docx import Document as DocxDocument
from loguru import logger

from app.core.config import settings

class DocumentProcessor:
    def __init__(self):
        self.nlp = None
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP models"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
                
        except Exception as e:
            logger.error(f"Failed to initialize NLP models: {e}")
    
    async def process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process PDF file and extract text"""
        try:
            logger.info(f"Processing PDF: {filename}")
            
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append({
                            'page': page_num + 1,
                            'text': page_text.strip()
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
            
            if not text_content:
                raise ValueError("No text content found in PDF")
            
            # Combine all text
            full_text = "\n\n".join([page['text'] for page in text_content])
            
            # Clean text
            cleaned_text = self.clean_text(full_text)
            
            # Create chunks
            chunks = self.create_chunks(cleaned_text)
            
            # Extract metadata
            metadata = await self.extract_metadata(cleaned_text)
            
            result = {
                'text': cleaned_text,
                'pages': text_content,
                'chunks': chunks,
                'metadata': {
                    'filename': filename,
                    'total_pages': len(pdf_reader.pages),
                    'total_chunks': len(chunks),
                    'total_characters': len(cleaned_text),
                    **metadata
                }
            }
            
            logger.info(f"Successfully processed PDF: {filename} - {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process PDF {filename}: {e}")
            raise
    
    async def process_docx(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process DOCX file and extract text"""
        try:
            logger.info(f"Processing DOCX: {filename}")
            
            doc = DocxDocument(BytesIO(file_content))
            
            # Extract text from paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
            
            if not paragraphs:
                raise ValueError("No text content found in DOCX")
            
            # Combine all text
            full_text = "\n\n".join(paragraphs)
            
            # Clean text
            cleaned_text = self.clean_text(full_text)
            
            # Create chunks
            chunks = self.create_chunks(cleaned_text)
            
            # Extract metadata
            metadata = await self.extract_metadata(cleaned_text)
            
            result = {
                'text': cleaned_text,
                'paragraphs': paragraphs,
                'chunks': chunks,
                'metadata': {
                    'filename': filename,
                    'total_paragraphs': len(paragraphs),
                    'total_chunks': len(chunks),
                    'total_characters': len(cleaned_text),
                    **metadata
                }
            }
            
            logger.info(f"Successfully processed DOCX: {filename} - {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process DOCX {filename}: {e}")
            raise
    
    async def process_text(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process plain text file"""
        try:
            logger.info(f"Processing text file: {filename}")
            
            # Decode text
            text = file_content.decode('utf-8')
            
            if not text.strip():
                raise ValueError("No text content found in file")
            
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # Create chunks
            chunks = self.create_chunks(cleaned_text)
            
            # Extract metadata
            metadata = await self.extract_metadata(cleaned_text)
            
            result = {
                'text': cleaned_text,
                'chunks': chunks,
                'metadata': {
                    'filename': filename,
                    'total_chunks': len(chunks),
                    'total_characters': len(cleaned_text),
                    **metadata
                }
            }
            
            logger.info(f"Successfully processed text file: {filename} - {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process text file {filename}: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep punctuation
        import re
        text = re.sub(r'[^\w\s.,!?;:()\-"\'']', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_chunks(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """Create text chunks with overlap"""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        # Split into sentences
        sentences = self.split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append({
                    'index': chunk_index,
                    'text': current_chunk.strip(),
                    'size': len(current_chunk.strip()),
                    'start_pos': len(' '.join([chunk['text'] for chunk in chunks]))
                })
                
                # Start new chunk with overlap
                overlap_text = self.get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + ' ' + sentence if overlap_text else sentence
                current_size = len(current_chunk)
                chunk_index += 1
            else:
                current_chunk += (' ' + sentence) if current_chunk else sentence
                current_size += sentence_size
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'index': chunk_index,
                'text': current_chunk.strip(),
                'size': len(current_chunk.strip()),
                'start_pos': len(' '.join([chunk['text'] for chunk in chunks]))
            })
        
        return [chunk for chunk in chunks if len(chunk['text']) > 50]  # Filter very short chunks
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except:
            # Fallback: simple sentence splitting
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of current chunk"""
        words = text.split()
        overlap_words = min(overlap_size // 6, len(words))  # Approximate 6 chars per word
        return ' '.join(words[-overlap_words:]) if overlap_words > 0 else ""
    
    async def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text using NLP"""
        metadata = {
            'entities': [],
            'keywords': [],
            'language': 'en',
            'readability_score': 0.0
        }
        
        try:
            if self.nlp:
                # Process with spaCy
                doc = self.nlp(text[:1000000])  # Limit text size for processing
                
                # Extract entities
                entities = {}
                for ent in doc.ents:
                    if ent.label_ not in entities:
                        entities[ent.label_] = []
                    entities[ent.label_].append(ent.text)
                
                metadata['entities'] = entities
                
                # Extract keywords (noun phrases)
                keywords = []
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) <= 3:  # Limit to 3-word phrases
                        keywords.append(chunk.text.lower())
                
                metadata['keywords'] = list(set(keywords))[:20]  # Top 20 unique keywords
            
            # Calculate basic readability score
            sentences = self.split_into_sentences(text)
            words = text.split()
            
            if sentences and words:
                avg_sentence_length = len(words) / len(sentences)
                metadata['readability_score'] = min(100, max(0, 100 - avg_sentence_length))
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
        
        return metadata
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()

# Global instance
document_processor = DocumentProcessor()