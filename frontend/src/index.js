import './styles/main.css';
import PDFProcessor from './utils/pdfProcessor.js';
import DocumentSearch from './utils/documentSearch.js';

class ResearchChatApp {
  constructor() {
    this.pdfProcessor = new PDFProcessor();
    this.documentSearch = new DocumentSearch(this.pdfProcessor);
    this.activeDocuments = [];
    this.chatHistory = [];
    this.isSidebarOpen = false;
    
    this.initializeElements();
    this.bindEvents();
    this.loadStoredDocuments();
  }

  initializeElements() {
    // Main elements
    this.uploadBtn = document.getElementById('uploadBtn');
    this.demoBtn = document.getElementById('demoBtn');
    this.fileInput = document.getElementById('fileInput');
    this.documentList = document.getElementById('documentList');
    this.chatMessages = document.getElementById('chatMessages');
    this.chatInput = document.getElementById('chatInput');
    this.sendBtn = document.getElementById('sendBtn');
    this.loadingOverlay = document.getElementById('loadingOverlay');
    this.sidebarToggle = document.getElementById('sidebarToggle');
    this.documentSidebar = document.getElementById('documentSidebar');
    this.inputHint = document.querySelector('.input-hint');
  }

  bindEvents() {
    // File upload events
    this.uploadBtn.addEventListener('click', () => this.fileInput.click());
    this.demoBtn.addEventListener('click', () => this.addDemoDocuments());
    this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e.target.files));
    
    // Chat events
    this.sendBtn.addEventListener('click', () => this.handleSendMessage());
    this.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSendMessage();
      }
    });
    
    // Auto-resize textarea
    this.chatInput.addEventListener('input', () => this.autoResizeTextarea());
    
    // Sidebar toggle for mobile
    this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
    
    // Drag and drop
    this.setupDragAndDrop();
    
    // Window resize
    window.addEventListener('resize', () => this.handleResize());
  }

  setupDragAndDrop() {
    const dropZones = [this.documentSidebar, this.chatMessages];
    
    dropZones.forEach(zone => {
      zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
      });
      
      zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
      });
      
      zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf');
        if (files.length > 0) {
          this.handleFileUpload(files);
        }
      });
    });
  }

  async handleFileUpload(files) {
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length === 0) {
      this.showNotification('Please upload PDF files only.', 'error');
      return;
    }

    this.showLoading('Processing documents...');
    
    try {
      for (const file of pdfFiles) {
        const document = await this.pdfProcessor.processFile(file);
        this.addDocumentToUI(document);
        this.activeDocuments.push(document.id);
      }
      
      this.updateChatInputState();
      this.saveDocuments();
      this.showNotification(`Successfully processed ${pdfFiles.length} document(s)`, 'success');
      
    } catch (error) {
      console.error('Error processing files:', error);
      this.showNotification('Error processing documents. Please try again.', 'error');
    } finally {
      this.hideLoading();
    }
  }

  addDocumentToUI(document) {
    // Remove empty state if it exists
    const emptyState = this.documentList.querySelector('.empty-state');
    if (emptyState) {
      emptyState.remove();
    }

    const documentItem = document.createElement('div');
    documentItem.className = 'document-item';
    documentItem.dataset.documentId = document.id;
    
    documentItem.innerHTML = `
      <div class="document-name" title="${document.name}">${document.name}</div>
      <div class="document-info">
        <span class="document-pages">${document.pages} pages</span>
        <span class="document-size">${document.size}</span>
      </div>
      <div class="processing-indicator" style="display: none;">
        Processing document...
      </div>
    `;
    
    documentItem.addEventListener('click', () => this.toggleDocumentSelection(document.id));
    
    this.documentList.appendChild(documentItem);
  }

  toggleDocumentSelection(documentId) {
    const documentItem = this.documentList.querySelector(`[data-document-id="${documentId}"]`);
    
    if (this.activeDocuments.includes(documentId)) {
      // Deselect
      this.activeDocuments = this.activeDocuments.filter(id => id !== documentId);
      documentItem.classList.remove('active');
    } else {
      // Select
      this.activeDocuments.push(documentId);
      documentItem.classList.add('active');
    }
    
    this.updateChatInputState();
  }

  updateChatInputState() {
    const hasDocuments = this.pdfProcessor.getAllDocuments().length > 0;
    
    this.chatInput.disabled = !hasDocuments;
    this.sendBtn.disabled = !hasDocuments;
    
    if (hasDocuments) {
      this.chatInput.placeholder = 'Ask a question about your research papers...';
      this.inputHint.textContent = `${this.activeDocuments.length || 'All'} document(s) selected for search`;
    } else {
      this.chatInput.placeholder = 'Upload research papers to start asking questions...';
      this.inputHint.textContent = 'Upload research papers to start asking questions';
    }
  }

  async handleSendMessage() {
    const message = this.chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    this.addMessageToChat(message, 'user');
    this.chatInput.value = '';
    this.autoResizeTextarea();

    // Show typing indicator
    const typingId = this.showTypingIndicator();

    try {
      // Process the query
      const searchDocuments = this.activeDocuments.length > 0 ? this.activeDocuments : null;
      const result = await this.documentSearch.processQuery(message, searchDocuments);
      
      // Remove typing indicator
      this.removeTypingIndicator(typingId);
      
      // Add assistant response
      this.addMessageToChat(result.response, 'assistant', result.citations);
      
    } catch (error) {
      console.error('Error processing query:', error);
      this.removeTypingIndicator(typingId);
      this.addMessageToChat('Sorry, I encountered an error while processing your question. Please try again.', 'assistant');
    }
  }

  addMessageToChat(content, sender, citations = []) {
    // Remove welcome message if it exists
    const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
      welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : 'A';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Process content with citations
    let processedContent = content;
    if (citations && citations.length > 0) {
      citations.forEach((citation, index) => {
        const citationSpan = `<span class="citation" data-citation="${index + 1}" title="${citation.document}">[${index + 1}]</span>`;
        processedContent = processedContent.replace(`[${index + 1}]`, citationSpan);
      });
    }
    
    messageContent.innerHTML = this.formatMessageContent(processedContent);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    this.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();
    
    // Store in chat history
    this.chatHistory.push({
      content,
      sender,
      citations,
      timestamp: new Date()
    });
  }

  formatMessageContent(content) {
    // Convert markdown-like formatting
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
    
    return `<p>${formatted}</p>`;
  }

  showTypingIndicator() {
    const typingId = Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing';
    typingDiv.dataset.typingId = typingId;
    
    typingDiv.innerHTML = `
      <div class="message-avatar">A</div>
      <div class="message-content">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    
    this.chatMessages.appendChild(typingDiv);
    this.scrollToBottom();
    
    return typingId;
  }

  removeTypingIndicator(typingId) {
    const typingElement = this.chatMessages.querySelector(`[data-typing-id="${typingId}"]`);
    if (typingElement) {
      typingElement.remove();
    }
  }

  autoResizeTextarea() {
    this.chatInput.style.height = 'auto';
    this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
  }

  scrollToBottom() {
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
    this.documentSidebar.classList.toggle('open', this.isSidebarOpen);
  }

  handleResize() {
    if (window.innerWidth > 768) {
      this.documentSidebar.classList.remove('open');
      this.isSidebarOpen = false;
    }
  }

  showLoading(message) {
    this.loadingOverlay.querySelector('p').textContent = message;
    this.loadingOverlay.style.display = 'flex';
  }

  hideLoading() {
    this.loadingOverlay.style.display = 'none';
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <span>${message}</span>
      <button class="notification-close">&times;</button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, 5000);
    
    // Manual close
    notification.querySelector('.notification-close').addEventListener('click', () => {
      notification.remove();
    });
  }

  saveDocuments() {
    try {
      const documentData = this.pdfProcessor.getAllDocuments().map(doc => ({
        id: doc.id,
        name: doc.name,
        size: doc.size,
        pages: doc.pages,
        content: doc.content,
        pageContents: doc.pageContents,
        uploadDate: doc.uploadDate
      }));
      
      localStorage.setItem('researchDocuments', JSON.stringify(documentData));
    } catch (error) {
      console.warn('Could not save documents to localStorage:', error);
    }
  }

  loadStoredDocuments() {
    try {
      const stored = localStorage.getItem('researchDocuments');
      if (stored) {
        const documentData = JSON.parse(stored);
        
        documentData.forEach(docData => {
          // Recreate document object
          this.pdfProcessor.documents.set(docData.id, {
            ...docData,
            uploadDate: new Date(docData.uploadDate)
          });
          
          this.addDocumentToUI(docData);
        });
        
        this.updateChatInputState();
      }
    } catch (error) {
      console.warn('Could not load stored documents:', error);
    }
  }

  // Demo function to add sample documents for testing
  addDemoDocuments() {
    // Clear existing documents first
    this.pdfProcessor.documents.clear();
    this.documentList.innerHTML = '';
    this.activeDocuments = [];

    const demoDocuments = [
      {
        id: 'demo1',
        name: 'Machine Learning in Healthcare.pdf',
        size: '2.3 MB',
        pages: 24,
        content: 'Machine learning is revolutionizing healthcare through predictive analytics, diagnostic assistance, and treatment optimization. Recent studies show that ML algorithms can predict patient outcomes with 85% accuracy. Diagnostic imaging enhanced by deep learning models shows improved detection rates for early-stage diseases. Treatment personalization using ML helps optimize drug dosages and reduces adverse effects.',
        pageContents: ['Introduction to ML in healthcare...', 'Predictive analytics applications...'],
        uploadDate: new Date()
      },
      {
        id: 'demo2',
        name: 'Quantum Computing Research.pdf',
        size: '1.8 MB',
        pages: 18,
        content: 'Quantum computing represents a paradigm shift in computational power. Current research focuses on quantum supremacy, error correction, and practical applications. Quantum algorithms like Shor\'s algorithm demonstrate exponential speedup for factoring large numbers. Applications in cryptography, optimization, and drug discovery show promising results.',
        pageContents: ['Quantum computing fundamentals...', 'Current research directions...'],
        uploadDate: new Date()
      }
    ];

    demoDocuments.forEach(doc => {
      this.pdfProcessor.documents.set(doc.id, doc);
      this.addDocumentToUI(doc);
      this.activeDocuments.push(doc.id);
    });

    this.updateChatInputState();
    this.showNotification('Demo documents loaded! You can now ask questions about machine learning and quantum computing.', 'success');
  }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new ResearchChatApp();
});