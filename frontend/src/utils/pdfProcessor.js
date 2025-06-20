import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js`;

export class PDFProcessor {
  constructor() {
    this.documents = new Map();
  }

  async processFile(file) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      
      const document = {
        id: this.generateId(),
        name: file.name,
        size: this.formatFileSize(file.size),
        pages: pdf.numPages,
        content: '',
        pageContents: [],
        uploadDate: new Date(),
        file: file
      };

      // Extract text from all pages
      const pagePromises = [];
      for (let i = 1; i <= pdf.numPages; i++) {
        pagePromises.push(this.extractPageText(pdf, i));
      }

      const pageTexts = await Promise.all(pagePromises);
      document.pageContents = pageTexts;
      document.content = pageTexts.join('\n\n--- Page Break ---\n\n');

      this.documents.set(document.id, document);
      return document;
    } catch (error) {
      console.error('Error processing PDF:', error);
      throw new Error(`Failed to process PDF: ${error.message}`);
    }
  }

  async extractPageText(pdf, pageNumber) {
    try {
      const page = await pdf.getPage(pageNumber);
      const textContent = await page.getTextContent();
      
      // Combine text items with proper spacing
      const text = textContent.items
        .map(item => item.str)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();
      
      return text;
    } catch (error) {
      console.error(`Error extracting text from page ${pageNumber}:`, error);
      return '';
    }
  }

  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getDocument(id) {
    return this.documents.get(id);
  }

  getAllDocuments() {
    return Array.from(this.documents.values());
  }

  removeDocument(id) {
    return this.documents.delete(id);
  }

  searchInDocuments(query, documentIds = null) {
    const searchResults = [];
    const docsToSearch = documentIds 
      ? documentIds.map(id => this.documents.get(id)).filter(Boolean)
      : this.getAllDocuments();

    const queryLower = query.toLowerCase();

    for (const doc of docsToSearch) {
      const matches = this.findMatches(doc.content, queryLower);
      if (matches.length > 0) {
        searchResults.push({
          document: doc,
          matches: matches.slice(0, 5) // Limit to top 5 matches per document
        });
      }
    }

    return searchResults;
  }

  findMatches(text, query) {
    const matches = [];
    const textLower = text.toLowerCase();
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    sentences.forEach((sentence, index) => {
      if (sentence.toLowerCase().includes(query)) {
        const contextStart = Math.max(0, index - 1);
        const contextEnd = Math.min(sentences.length - 1, index + 1);
        const context = sentences.slice(contextStart, contextEnd + 1).join('. ').trim();
        
        matches.push({
          text: sentence.trim(),
          context: context,
          score: this.calculateRelevanceScore(sentence.toLowerCase(), query)
        });
      }
    });

    return matches.sort((a, b) => b.score - a.score);
  }

  calculateRelevanceScore(text, query) {
    let score = 0;
    const words = query.split(/\s+/);
    
    words.forEach(word => {
      const regex = new RegExp(word, 'gi');
      const matches = (text.match(regex) || []).length;
      score += matches;
    });

    // Boost score for exact phrase matches
    if (text.includes(query)) {
      score += 10;
    }

    return score;
  }

  getDocumentStats() {
    const docs = this.getAllDocuments();
    return {
      totalDocuments: docs.length,
      totalPages: docs.reduce((sum, doc) => sum + doc.pages, 0),
      totalSize: docs.reduce((sum, doc) => {
        const sizeStr = doc.size;
        const sizeValue = parseFloat(sizeStr);
        const unit = sizeStr.split(' ')[1];
        let bytes = sizeValue;
        
        switch (unit) {
          case 'KB': bytes *= 1024; break;
          case 'MB': bytes *= 1024 * 1024; break;
          case 'GB': bytes *= 1024 * 1024 * 1024; break;
        }
        
        return sum + bytes;
      }, 0)
    };
  }
}

export default PDFProcessor;