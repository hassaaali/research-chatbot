import './styles/main.css';
import APIClient from './utils/api.js';

class ResearchChatApp {
  constructor() {
    this.apiClient = APIClient;
    this.activeDocuments = [];
    this.chatHistory = [];
    this.isSidebarOpen = false;
    this.isBackendConnected = false;
    
    this.initializeElements();
    this.bindEvents();
    this.checkBackendConnection();
    this.loadDocuments();
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

  async checkBackendConnection() {
    try {
      await this.apiClient.healthCheck();
      this.isBackendConnected = true;
      this.showNotification('Connected to backend server', 'success');
      this.updateChatInputState();
    } catch (error) {
      this.isBackendConnected = false;
      this.showNotification('Backend server not available. Please start the Python backend.', 'error');
      this.updateChatInputState();
    }
  }

  async loadDocuments() {
    if (!this.isBackendConnected) return;

    try {
      const response = await this.apiClient.getDocuments();
      if (response.success) {
        this.clearDocumentList();
        response.documents.forEach(doc => {
          this.addDocumentToUI(doc);
          if (doc.is_processed) {
            this.activeDocuments.push(doc.id.toString());
          }
        });
        this.updateChatInputState();
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  }

  clearDocumentList() {
    this.documentList.innerHTML = '';
    this.activeDocuments = [];
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
    if (!this.isBackendConnected) {
      this.showNotification('Backend server not available', 'error');
      return;
    }

    const pdfFiles = Array.from(files).filter(file => 
      file.type === 'application/pdf' || 
      file.name.endsWith('.pdf') ||
      file.name.endsWith('.txt') ||
      file.name.endsWith('.docx')
    );
    
    if (pdfFiles.length === 0) {
      this.showNotification('Please upload PDF, TXT, or DOCX files only.', 'error');
      return;
    }

    this.showLoading('Uploading and processing documents...');
    
    try {
      const response = await this.apiClient.uploadDocuments(pdfFiles);
      
      if (response.success) {
        this.showNotification(`Successfully uploaded ${pdfFiles.length} document(s)`, 'success');
        
        // Reload documents to get updated list
        await this.loadDocuments();
        
        // Poll for processing status
        response.documents.forEach(doc => {
          if (doc.status === 'uploaded') {
            this.pollDocumentStatus(doc.id);
          }
        });
      }
      
    } catch (error) {
      console.error('Error uploading files:', error);
      this.showNotification('Error uploading documents. Please try again.', 'error');
    } finally {
      this.hideLoading();
    }
  }

  async pollDocumentStatus(documentId) {
    const maxAttempts = 30; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await this.apiClient.getDocumentStatus(documentId);
        
        if (response.success) {
          const status = response.status;
          
          if (status.processing_status === 'completed') {
            // Reload documents to update UI
            await this.loadDocuments();
            this.showNotification('Document processing completed', 'success');
            return;
          } else if (status.processing_status === 'failed') {
            this.showNotification(`Document processing failed: ${status.error_message}`, 'error');
            return;
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000); // Poll every 10 seconds
        }
        
      } catch (error) {
        console.error('Error polling document status:', error);
      }
    };

    poll();
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
    
    const statusClass = document.is_processed ? 'processed' : 
                       document.processing_status === 'processing' ? 'processing' : 
                       document.processing_status === 'failed' ? 'failed' : 'pending';
    
    documentItem.innerHTML = `
      <div class="document-name" title="${document.original_filename}">${document.original_filename}</div>
      <div class="document-info">
        <span class="document-pages">${document.total_pages || 0} pages</span>
        <span class="document-size">${this.formatFileSize(document.file_size)}</span>
      </div>
      <div class="document-status ${statusClass}">
        ${this.getStatusText(document.processing_status, document.is_processed)}
      </div>
    `;
    
    if (document.is_processed) {
      documentItem.addEventListener('click', () => this.toggleDocumentSelection(document.id.toString()));
    }
    
    this.documentList.appendChild(documentItem);
  }

  getStatusText(processingStatus, isProcessed) {
    if (isProcessed) return '✅ Ready';
    if (processingStatus === 'processing') return '⏳ Processing...';
    if (processingStatus === 'failed') return '❌ Failed';
    return '⏳ Pending...';
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
    const hasBackend = this.isBackendConnected;
    const hasProcessedDocs = this.documentList.querySelectorAll('.document-item .document-status.processed').length > 0;
    
    this.chatInput.disabled = !hasBackend || !hasProcessedDocs;
    this.sendBtn.disabled = !hasBackend || !hasProcessedDocs;
    
    if (!hasBackend) {
      this.chatInput.placeholder = 'Backend server not available...';
      this.inputHint.textContent = 'Please start the Python backend server';
    } else if (!hasProcessedDocs) {
      this.chatInput.placeholder = 'Upload and process documents to start asking questions...';
      this.inputHint.textContent = 'Upload research papers to start asking questions';
    } else {
      this.chatInput.placeholder = 'Ask a question about your research papers...';
      this.inputHint.textContent = `${this.activeDocuments.length || 'All'} document(s) selected for search`;
    }
  }

  async handleSendMessage() {
    const message = this.chatInput.value.trim();
    if (!message || !this.isBackendConnected) return;

    // Add user message to chat
    this.addMessageToChat(message, 'user');
    this.chatInput.value = '';
    this.autoResizeTextarea();

    // Show typing indicator
    const typingId = this.showTypingIndicator();

    try {
      // Send message to backend
      const response = await this.apiClient.sendMessage(message, {
        documentIds: this.activeDocuments.length > 0 ? this.activeDocuments : null,
        includeWebSearch: true
      });
      
      // Remove typing indicator
      this.removeTypingIndicator(typingId);
      
      // Add assistant response
      this.addMessageToChat(response.answer, 'assistant', response.sources);
      
    } catch (error) {
      console.error('Error processing query:', error);
      this.removeTypingIndicator(typingId);
      this.addMessageToChat('Sorry, I encountered an error while processing your question. Please try again.', 'assistant');
    }
  }

  addMessageToChat(content, sender, sources = null) {
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
    
    // Format content
    let formattedContent = this.formatMessageContent(content);
    
    // Add sources if available
    if (sources && sender === 'assistant') {
      formattedContent += this.formatSources(sources);
    }
    
    messageContent.innerHTML = formattedContent;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    this.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();
    
    // Store in chat history
    this.chatHistory.push({
      content,
      sender,
      sources,
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

  formatSources(sources) {
    let sourcesHtml = '';
    
    if (sources.documents && sources.documents.length > 0) {
      sourcesHtml += '<div class="sources"><h4>Document Sources:</h4><ul>';
      sources.documents.forEach((source, index) => {
        sourcesHtml += `<li><strong>Document ${source.document_id}</strong> (Similarity: ${(source.similarity * 100).toFixed(1)}%)</li>`;
      });
      sourcesHtml += '</ul></div>';
    }
    
    if (sources.web && sources.web.length > 0) {
      sourcesHtml += '<div class="sources"><h4>Web Sources:</h4><ul>';
      sources.web.forEach((source, index) => {
        sourcesHtml += `<li><a href="${source.url}" target="_blank">${source.title}</a></li>`;
      });
      sourcesHtml += '</ul></div>';
    }
    
    return sourcesHtml;
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

  // Demo function - now uses backend
  async addDemoDocuments() {
    this.showNotification('Demo mode now requires uploading actual documents. Please use the upload button to add your research papers.', 'info');
  }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new ResearchChatApp();
});