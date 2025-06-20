import fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import logger from '../utils/logger.js';
import embeddingService from './embeddings.js';

class VectorStore {
  constructor() {
    this.vectors = new Map();
    this.metadata = new Map();
    this.storePath = process.env.VECTOR_DB_PATH || './data/vectors';
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      await fs.mkdir(this.storePath, { recursive: true });
      await this.loadFromDisk();
      this.isInitialized = true;
      logger.info('Vector store initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize vector store:', error);
      throw error;
    }
  }

  async addDocument(documentId, chunks, metadata = {}) {
    try {
      logger.info(`Adding document ${documentId} with ${chunks.length} chunks to vector store`);
      
      const embeddings = await embeddingService.generateBatchEmbeddings(chunks);
      
      for (let i = 0; i < chunks.length; i++) {
        const chunkId = `${documentId}_chunk_${i}`;
        
        this.vectors.set(chunkId, embeddings[i]);
        this.metadata.set(chunkId, {
          documentId,
          chunkIndex: i,
          text: chunks[i],
          ...metadata,
          createdAt: new Date().toISOString()
        });
      }

      await this.saveToDisk();
      logger.info(`Successfully added ${chunks.length} chunks for document ${documentId}`);
      
      return {
        documentId,
        chunksAdded: chunks.length,
        totalVectors: this.vectors.size
      };
    } catch (error) {
      logger.error(`Failed to add document ${documentId} to vector store:`, error);
      throw error;
    }
  }

  async search(queryText, topK = 10, documentIds = null) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const queryEmbedding = await embeddingService.generateEmbedding(queryText);
      const results = [];

      for (const [chunkId, vector] of this.vectors.entries()) {
        const metadata = this.metadata.get(chunkId);
        
        // Filter by document IDs if specified
        if (documentIds && !documentIds.includes(metadata.documentId)) {
          continue;
        }

        const similarity = embeddingService.calculateSimilarity(queryEmbedding, vector);
        
        results.push({
          chunkId,
          similarity,
          metadata,
          text: metadata.text
        });
      }

      // Sort by similarity and return top K
      results.sort((a, b) => b.similarity - a.similarity);
      return results.slice(0, topK);
    } catch (error) {
      logger.error('Failed to search vector store:', error);
      throw error;
    }
  }

  async removeDocument(documentId) {
    try {
      const chunksToRemove = [];
      
      for (const [chunkId, metadata] of this.metadata.entries()) {
        if (metadata.documentId === documentId) {
          chunksToRemove.push(chunkId);
        }
      }

      for (const chunkId of chunksToRemove) {
        this.vectors.delete(chunkId);
        this.metadata.delete(chunkId);
      }

      await this.saveToDisk();
      logger.info(`Removed ${chunksToRemove.length} chunks for document ${documentId}`);
      
      return { removedChunks: chunksToRemove.length };
    } catch (error) {
      logger.error(`Failed to remove document ${documentId} from vector store:`, error);
      throw error;
    }
  }

  async getDocumentStats() {
    const documentStats = new Map();
    
    for (const metadata of this.metadata.values()) {
      const docId = metadata.documentId;
      if (!documentStats.has(docId)) {
        documentStats.set(docId, {
          documentId: docId,
          chunkCount: 0,
          totalCharacters: 0
        });
      }
      
      const stats = documentStats.get(docId);
      stats.chunkCount++;
      stats.totalCharacters += metadata.text.length;
    }

    return {
      totalDocuments: documentStats.size,
      totalChunks: this.vectors.size,
      documents: Array.from(documentStats.values())
    };
  }

  async saveToDisk() {
    try {
      const vectorsPath = path.join(this.storePath, 'vectors.json');
      const metadataPath = path.join(this.storePath, 'metadata.json');

      const vectorsData = Object.fromEntries(this.vectors);
      const metadataData = Object.fromEntries(this.metadata);

      await Promise.all([
        fs.writeFile(vectorsPath, JSON.stringify(vectorsData, null, 2)),
        fs.writeFile(metadataPath, JSON.stringify(metadataData, null, 2))
      ]);
    } catch (error) {
      logger.error('Failed to save vector store to disk:', error);
      throw error;
    }
  }

  async loadFromDisk() {
    try {
      const vectorsPath = path.join(this.storePath, 'vectors.json');
      const metadataPath = path.join(this.storePath, 'metadata.json');

      const [vectorsExist, metadataExist] = await Promise.all([
        fs.access(vectorsPath).then(() => true).catch(() => false),
        fs.access(metadataPath).then(() => true).catch(() => false)
      ]);

      if (vectorsExist && metadataExist) {
        const [vectorsData, metadataData] = await Promise.all([
          fs.readFile(vectorsPath, 'utf-8').then(JSON.parse),
          fs.readFile(metadataPath, 'utf-8').then(JSON.parse)
        ]);

        this.vectors = new Map(Object.entries(vectorsData));
        this.metadata = new Map(Object.entries(metadataData));

        logger.info(`Loaded ${this.vectors.size} vectors from disk`);
      }
    } catch (error) {
      logger.warn('Could not load vector store from disk:', error);
      // Initialize empty stores
      this.vectors = new Map();
      this.metadata = new Map();
    }
  }
}

const vectorStore = new VectorStore();

export async function initializeVectorStore() {
  await vectorStore.initialize();
}

export default vectorStore;