import pdfParse from 'pdf-parse';
import natural from 'natural';
import compromise from 'compromise';
import logger from '../utils/logger.js';

class DocumentProcessor {
  constructor() {
    this.tokenizer = new natural.WordTokenizer();
    this.stemmer = natural.PorterStemmer;
  }

  async processPDF(buffer, filename) {
    try {
      logger.info(`Processing PDF: ${filename}`);
      
      const data = await pdfParse(buffer);
      const text = data.text;
      
      if (!text || text.trim().length === 0) {
        throw new Error('No text content found in PDF');
      }

      // Extract metadata
      const metadata = {
        filename,
        pages: data.numpages,
        info: data.info || {},
        processedAt: new Date().toISOString()
      };

      // Clean and process text
      const cleanedText = this.cleanText(text);
      const chunks = this.chunkText(cleanedText);
      const entities = this.extractEntities(cleanedText);
      const keywords = this.extractKeywords(cleanedText);

      logger.info(`Successfully processed PDF: ${filename} - ${chunks.length} chunks created`);

      return {
        text: cleanedText,
        chunks,
        metadata: {
          ...metadata,
          entities,
          keywords,
          chunkCount: chunks.length,
          characterCount: cleanedText.length
        }
      };
    } catch (error) {
      logger.error(`Failed to process PDF ${filename}:`, error);
      throw error;
    }
  }

  cleanText(text) {
    return text
      // Remove excessive whitespace
      .replace(/\s+/g, ' ')
      // Remove page numbers and headers/footers patterns
      .replace(/^\d+\s*$/gm, '')
      // Remove URLs
      .replace(/https?:\/\/[^\s]+/g, '')
      // Remove email addresses
      .replace(/\S+@\S+\.\S+/g, '')
      // Remove special characters but keep punctuation
      .replace(/[^\w\s.,!?;:()\-"']/g, ' ')
      // Clean up multiple spaces again
      .replace(/\s+/g, ' ')
      .trim();
  }

  chunkText(text, maxChunkSize = 1000, overlap = 200) {
    const sentences = this.splitIntoSentences(text);
    const chunks = [];
    let currentChunk = '';
    let currentSize = 0;

    for (const sentence of sentences) {
      const sentenceSize = sentence.length;
      
      // If adding this sentence would exceed the max size, save current chunk
      if (currentSize + sentenceSize > maxChunkSize && currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
        
        // Start new chunk with overlap
        const overlapText = this.getOverlapText(currentChunk, overlap);
        currentChunk = overlapText + ' ' + sentence;
        currentSize = currentChunk.length;
      } else {
        currentChunk += (currentChunk ? ' ' : '') + sentence;
        currentSize += sentenceSize;
      }
    }

    // Add the last chunk if it has content
    if (currentChunk.trim().length > 0) {
      chunks.push(currentChunk.trim());
    }

    return chunks.filter(chunk => chunk.length > 50); // Filter out very short chunks
  }

  splitIntoSentences(text) {
    // Use compromise for better sentence splitting
    const doc = compromise(text);
    return doc.sentences().out('array');
  }

  getOverlapText(text, overlapSize) {
    const words = text.split(' ');
    const overlapWords = Math.min(Math.floor(overlapSize / 6), words.length); // Approximate 6 chars per word
    return words.slice(-overlapWords).join(' ');
  }

  extractEntities(text) {
    try {
      const doc = compromise(text);
      
      return {
        people: doc.people().out('array'),
        places: doc.places().out('array'),
        organizations: doc.organizations().out('array'),
        dates: doc.dates().out('array'),
        topics: doc.topics().out('array')
      };
    } catch (error) {
      logger.warn('Failed to extract entities:', error);
      return {
        people: [],
        places: [],
        organizations: [],
        dates: [],
        topics: []
      };
    }
  }

  extractKeywords(text, topK = 20) {
    try {
      // Tokenize and clean
      const tokens = this.tokenizer.tokenize(text.toLowerCase());
      const stopWords = new Set(natural.stopwords);
      
      // Filter tokens
      const filteredTokens = tokens.filter(token => 
        token.length > 2 && 
        !stopWords.has(token) && 
        /^[a-zA-Z]+$/.test(token)
      );

      // Calculate TF-IDF scores (simplified)
      const termFreq = {};
      filteredTokens.forEach(token => {
        const stemmed = this.stemmer.stem(token);
        termFreq[stemmed] = (termFreq[stemmed] || 0) + 1;
      });

      // Sort by frequency and return top keywords
      const sortedTerms = Object.entries(termFreq)
        .sort(([,a], [,b]) => b - a)
        .slice(0, topK)
        .map(([term, freq]) => ({ term, frequency: freq }));

      return sortedTerms;
    } catch (error) {
      logger.warn('Failed to extract keywords:', error);
      return [];
    }
  }

  async processMultipleDocuments(documents) {
    const results = [];
    
    for (const doc of documents) {
      try {
        const result = await this.processPDF(doc.buffer, doc.filename);
        results.push({
          success: true,
          filename: doc.filename,
          ...result
        });
      } catch (error) {
        results.push({
          success: false,
          filename: doc.filename,
          error: error.message
        });
      }
    }

    return results;
  }
}

export default new DocumentProcessor();