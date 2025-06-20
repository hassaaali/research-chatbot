# Research Paper RAG Chatbot

A comprehensive Research Assistant application that combines a modern web frontend with a powerful Python backend featuring RAG (Retrieval-Augmented Generation) capabilities. Upload research papers and have intelligent conversations about their content using state-of-the-art language models.

## 🚀 Features

### Frontend (JavaScript/HTML/CSS)
- **Modern ChatGPT-style Interface**: Clean, responsive design optimized for research workflows
- **Document Management**: Upload, view, and manage research papers with real-time processing status
- **Interactive Chat**: Smooth conversational interface with typing indicators and message history
- **Drag & Drop Support**: Easy document upload with visual feedback
- **Mobile Responsive**: Optimized for both desktop and mobile devices

### Backend (Python/FastAPI)
- **RAG Pipeline**: Advanced Retrieval-Augmented Generation using vector search and LLMs
- **Document Processing**: Support for PDF, DOCX, and TXT files with intelligent text extraction
- **Vector Search**: FAISS-powered semantic search across document collections
- **Hugging Face Integration**: State-of-the-art language models for response generation
- **Web Search Enhancement**: Optional web search integration for broader context
- **RESTful API**: Comprehensive API for document management and chat functionality

## 🏗️ Architecture

```
Frontend (JavaScript)     Backend (Python/FastAPI)
├── Modern Web UI        ├── Document Processing
├── Real-time Chat       ├── Vector Store (FAISS)
├── File Management      ├── Embedding Service
└── API Integration      ├── LLM Service (Hugging Face)
                        ├── Web Search Service
                        └── RAG Pipeline
```

## 📋 Prerequisites

### Backend Requirements
- Python 3.8+
- pip (Python package manager)

### Frontend Requirements
- Modern web browser
- Node.js (for development server)

## 🛠️ Installation & Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Download required models
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env file with your configuration
```

### 2. Environment Configuration

Edit `backend/.env` file:

```env
# Hugging Face API Token (optional, for advanced models)
HUGGINGFACE_API_TOKEN=your_token_here

# Enable web search (optional)
ENABLE_WEB_SEARCH=True
SEARCH_ENGINE=duckduckgo

# Adjust model settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TEXT_GENERATION_MODEL=microsoft/DialoGPT-medium
```

### 3. Start the Backend Server

```bash
cd backend
python main.py
```

The backend will be available at `http://localhost:8000`

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🎯 Usage

### 1. Upload Documents
- Click "Upload Papers" or drag & drop PDF/DOCX/TXT files
- Monitor processing status in the sidebar
- Documents are automatically processed and vectorized

### 2. Ask Questions
- Type questions about your uploaded research papers
- Select specific documents or search across all papers
- Get intelligent responses with source citations

### 3. Advanced Features
- **Web Search Integration**: Get additional context from academic sources
- **Document Summarization**: Generate summaries of your research collection
- **Similar Questions**: Get suggested follow-up questions
- **Chat History**: Review previous conversations

## 🔧 API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload documents
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Chat Interface
- `POST /api/chat/query` - Send chat message
- `GET /api/chat/sessions/{id}/history` - Get chat history
- `POST /api/chat/similar-questions` - Get similar questions
- `POST /api/chat/summarize` - Summarize documents

### Health & Status
- `GET /api/health` - Basic health check
- `GET /api/health/detailed` - Detailed service status

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `HUGGINGFACE_API_TOKEN` | Hugging Face API token | - |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `TEXT_GENERATION_MODEL` | Text generation model | `DialoGPT-medium` |
| `ENABLE_WEB_SEARCH` | Enable web search | `True` |
| `CHUNK_SIZE` | Document chunk size | `1000` |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | `5` |

### Model Options

#### Embedding Models
- `sentence-transformers/all-MiniLM-L6-v2` (Default, fast)
- `sentence-transformers/all-mpnet-base-v2` (Better quality)
- `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` (Q&A optimized)

#### Text Generation Models
- `microsoft/DialoGPT-medium` (Default, conversational)
- `mistralai/Mistral-7B-Instruct-v0.1` (Advanced, requires GPU)
- `google/flan-t5-base` (Instruction-tuned)

## 🚀 Deployment

### Backend Deployment

```bash
# Production setup
pip install gunicorn
gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment

```bash
cd frontend
npm run build
# Serve the dist/ directory with your web server
```

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Backend not starting**
   - Check Python version (3.8+ required)
   - Install missing dependencies: `pip install -r requirements.txt`
   - Download spaCy model: `python -m spacy download en_core_web_sm`

2. **Frontend can't connect to backend**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend configuration
   - Verify API URL in frontend configuration

3. **Document processing fails**
   - Check file format (PDF, DOCX, TXT supported)
   - Verify file size limits
   - Check backend logs for detailed error messages

4. **Poor response quality**
   - Try different embedding models
   - Adjust chunk size and overlap settings
   - Enable web search for additional context

### Performance Optimization

1. **GPU Acceleration**
   - Install PyTorch with CUDA support
   - Use GPU-optimized models
   - Set `device="cuda"` in model configuration

2. **Memory Management**
   - Reduce batch sizes for large documents
   - Use smaller embedding models for limited RAM
   - Implement document chunking strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)

## 🙏 Acknowledgments

- **Hugging Face** for transformer models and APIs
- **FAISS** for efficient vector search
- **FastAPI** for the robust backend framework
- **Sentence Transformers** for semantic embeddings
- **spaCy** for natural language processing

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ for researchers and academics**