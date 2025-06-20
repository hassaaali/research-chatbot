// API utility for communicating with Python backend
class APIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000/api';
    this.sessionId = this.generateSessionId();
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Document management
  async uploadDocuments(files) {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    return this.request('/documents/upload', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it with boundary
      body: formData
    });
  }

  async getDocuments() {
    return this.request('/documents');
  }

  async getDocument(documentId) {
    return this.request(`/documents/${documentId}`);
  }

  async deleteDocument(documentId) {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE'
    });
  }

  async getDocumentStatus(documentId) {
    return this.request(`/documents/${documentId}/status`);
  }

  // Chat functionality
  async sendMessage(message, options = {}) {
    return this.request('/chat/query', {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: this.sessionId,
        document_ids: options.documentIds,
        include_web_search: options.includeWebSearch !== false,
        max_tokens: options.maxTokens || 512,
        temperature: options.temperature || 0.7
      })
    });
  }

  async getChatHistory(sessionId = null) {
    const id = sessionId || this.sessionId;
    return this.request(`/chat/sessions/${id}/history`);
  }

  async getChatSessions() {
    return this.request('/chat/sessions');
  }

  async deleteChatSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    });
  }

  async getSimilarQuestions(question, documentIds = null) {
    return this.request('/chat/similar-questions', {
      method: 'POST',
      body: JSON.stringify({
        question,
        document_ids: documentIds
      })
    });
  }

  async summarizeDocuments(documentIds) {
    return this.request('/chat/summarize', {
      method: 'POST',
      body: JSON.stringify({
        document_ids: documentIds
      })
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }

  async detailedHealthCheck() {
    return this.request('/health/detailed');
  }
}

export default new APIClient();