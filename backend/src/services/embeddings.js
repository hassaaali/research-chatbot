import { pipeline } from '@xenova/transformers';
import logger from '../utils/logger.js';

class EmbeddingService {
  constructor() {
    this.model = null;
    this.modelName = 'sentence-transformers/all-MiniLM-L6-v2';
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      logger.info(`Loading embedding model: ${this.modelName}`);
      this.model = await pipeline('feature-extraction', this.modelName);
      this.isInitialized = true;
      logger.info('Embedding model loaded successfully');
    } catch (error) {
      logger.error('Failed to load embedding model:', error);
      throw error;
    }
  }

  async generateEmbedding(text) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      // Clean and prepare text
      const cleanText = this.preprocessText(text);
      
      // Generate embedding
      const output = await this.model(cleanText, { pooling: 'mean', normalize: true });
      
      // Convert to array if needed
      return Array.from(output.data);
    } catch (error) {
      logger.error('Failed to generate embedding:', error);
      throw error;
    }
  }

  async generateBatchEmbeddings(texts) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      const cleanTexts = texts.map(text => this.preprocessText(text));
      const embeddings = [];

      // Process in batches to avoid memory issues
      const batchSize = 10;
      for (let i = 0; i < cleanTexts.length; i += batchSize) {
        const batch = cleanTexts.slice(i, i + batchSize);
        const batchEmbeddings = await Promise.all(
          batch.map(text => this.generateEmbedding(text))
        );
        embeddings.push(...batchEmbeddings);
      }

      return embeddings;
    } catch (error) {
      logger.error('Failed to generate batch embeddings:', error);
      throw error;
    }
  }

  preprocessText(text) {
    if (!text || typeof text !== 'string') {
      return '';
    }

    return text
      .replace(/\s+/g, ' ')
      .replace(/[^\w\s.,!?-]/g, '')
      .trim()
      .substring(0, 512); // Limit to model's max length
  }

  calculateSimilarity(embedding1, embedding2) {
    if (!embedding1 || !embedding2 || embedding1.length !== embedding2.length) {
      return 0;
    }

    // Cosine similarity
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (let i = 0; i < embedding1.length; i++) {
      dotProduct += embedding1[i] * embedding2[i];
      norm1 += embedding1[i] * embedding1[i];
      norm2 += embedding2[i] * embedding2[i];
    }

    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }
}

const embeddingService = new EmbeddingService();

export async function initializeEmbeddingModel() {
  await embeddingService.initialize();
}

export default embeddingService;