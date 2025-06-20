# Research Paper Chat Assistant

A modern, ChatGPT-style web application that allows users to upload PDF research papers and have interactive conversations about their content.

## Features

### 🎯 Core Functionality
- **PDF Upload & Processing**: Upload multiple PDF research papers with drag-and-drop support
- **Text Extraction**: Automatic text extraction from PDF documents using PDF.js
- **Intelligent Search**: Advanced search functionality across all uploaded documents
- **Interactive Chat Interface**: ChatGPT-inspired conversational interface
- **Citation Support**: Responses include citations and references to source documents

### 🎨 User Interface
- **Modern Design**: Clean, professional interface inspired by ChatGPT
- **Responsive Layout**: Optimized for both desktop and mobile devices
- **Document Management**: Sidebar showing uploaded papers with metadata
- **Real-time Chat**: Smooth messaging experience with typing indicators
- **Progress Feedback**: Loading states and notifications for user actions

### 🔧 Technical Features
- **PDF.js Integration**: Client-side PDF processing and text extraction
- **Document Search**: Smart content matching and relevance scoring
- **Local Storage**: Persistent document storage across browser sessions
- **Error Handling**: Graceful error management and user feedback
- **Modular Architecture**: Clean separation of concerns with utility classes

## File Structure

```
./
├── src/
│   ├── index.js              # Main application entry point
│   ├── styles/
│   │   └── main.css          # Complete styling for the application
│   └── utils/
│       ├── pdfProcessor.js   # PDF processing and text extraction
│       └── documentSearch.js # Document search and query processing
├── public/
│   └── debug-bridge.js       # Development debugging utilities
├── index.html                # Main HTML template
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite configuration
└── eslint.config.js          # ESLint configuration
```

## How It Works

### 1. Document Upload
- Users can upload PDF files via the upload button or drag-and-drop
- Files are processed using PDF.js to extract text content
- Document metadata (name, size, pages) is stored and displayed

### 2. Text Processing
- PDF text is extracted page by page for accurate content retrieval
- Content is indexed for efficient searching
- Documents are stored locally for persistence

### 3. Question Processing
- User questions are analyzed to determine query type (definition, comparison, summary, etc.)
- Relevant content is searched across all uploaded documents
- Responses are generated with proper citations and context

### 4. Response Generation
- Intelligent response formatting based on query type
- Citation system links responses back to source documents
- Support for various query types: definitions, comparisons, summaries, methodologies

## Usage

### Getting Started
1. **Upload Documents**: Click "Upload Papers" or use the "Try Demo" button
2. **Ask Questions**: Type questions about your research papers in the chat input
3. **Review Responses**: Get detailed answers with citations and references

### Example Queries
- "What are the main findings of this research?"
- "Compare the methodologies used in these papers"
- "Summarize the conclusions about machine learning"
- "What are the limitations mentioned in the studies?"

### Demo Mode
Click "Try Demo" to load sample research papers and test the functionality without uploading real documents.

## Technologies Used

- **Frontend**: Vanilla JavaScript ES6+, Modern CSS, HTML5
- **PDF Processing**: PDF.js library for client-side PDF handling
- **Build Tool**: Vite for development and building
- **Styling**: CSS Grid/Flexbox, Custom animations, Responsive design
- **Storage**: Browser localStorage for document persistence

## Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Key Components

#### PDFProcessor
Handles PDF file processing, text extraction, and document management.

#### DocumentSearch
Manages search functionality, query processing, and response generation.

#### ResearchChatApp
Main application class that orchestrates the user interface and user interactions.

## Design Principles

### User Experience
- **Intuitive Interface**: Familiar ChatGPT-style design for immediate usability
- **Progressive Enhancement**: Features become available as documents are uploaded
- **Feedback-Rich**: Clear loading states, error messages, and success notifications

### Code Quality
- **Modular Design**: Separation of concerns with dedicated utility classes
- **Error Handling**: Comprehensive error management and user feedback
- **Performance**: Efficient text processing and search algorithms
- **Maintainability**: Clean, documented code with consistent patterns

## Browser Compatibility

- Modern browsers supporting ES6+ modules
- PDF.js compatibility for PDF processing
- Local storage support for document persistence

## Future Enhancements

- Advanced query types and natural language processing
- Document highlighting and annotation
- Export functionality for chat conversations
- Integration with external research databases
- Multi-language support for international papers