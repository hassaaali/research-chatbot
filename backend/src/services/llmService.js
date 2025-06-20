import { HfInference } from '@huggingface/inference';
import logger from '../utils/logger.js';

class LLMService {
  constructor() {
    this.hf = new HfInference(process.env.HUGGINGFACE_API_KEY);
    this.defaultModel = 'microsoft/DialoGPT-medium';
    this.textGenerationModel = 'mistralai/Mistral-7B-Instruct-v0.1';
  }

  async generateResponse(query, context, options = {}) {
    try {
      const {
        maxTokens = 512,
        temperature = 0.7,
        model = this.textGenerationModel
      } = options;

      const prompt = this.buildPrompt(query, context);
      
      logger.info(`Generating response for query: ${query.substring(0, 100)}...`);

      const response = await this.hf.textGeneration({
        model,
        inputs: prompt,
        parameters: {
          max_new_tokens: maxTokens,
          temperature,
          do_sample: true,
          top_p: 0.9,
          repetition_penalty: 1.1,
          return_full_text: false
        }
      });

      const generatedText = response.generated_text || '';
      const cleanedResponse = this.cleanResponse(generatedText);

      logger.info('Successfully generated LLM response');
      
      return {
        response: cleanedResponse,
        model: model,
        tokensUsed: this.estimateTokens(prompt + cleanedResponse)
      };
    } catch (error) {
      logger.error('Failed to generate LLM response:', error);
      
      // Fallback to a simpler response
      return {
        response: this.generateFallbackResponse(query, context),
        model: 'fallback',
        tokensUsed: 0,
        error: error.message
      };
    }
  }

  buildPrompt(query, context) {
    const contextText = context
      .map((item, index) => `[${index + 1}] ${item.text}`)
      .join('\n\n');

    return `You are a research assistant helping users understand academic papers. Use the provided context to answer the question accurately and comprehensively.

Context from research papers:
${contextText}

Question: ${query}

Instructions:
- Provide a detailed, accurate answer based on the context
- Include specific references to the papers when relevant
- If the context doesn't contain enough information, say so clearly
- Use academic language but keep it accessible
- Include citations in the format [1], [2], etc. referring to the context sources

Answer:`;
  }

  cleanResponse(response) {
    return response
      .replace(/^\s*Answer:\s*/i, '')
      .replace(/\n\s*\n/g, '\n\n')
      .trim();
  }

  generateFallbackResponse(query, context) {
    if (context.length === 0) {
      return "I don't have enough information in the uploaded documents to answer your question. Please make sure you've uploaded relevant research papers.";
    }

    // Simple extractive response as fallback
    const relevantChunks = context.slice(0, 3);
    let response = "Based on the research papers, here's what I found:\n\n";
    
    relevantChunks.forEach((chunk, index) => {
      response += `${chunk.text.substring(0, 200)}... [${index + 1}]\n\n`;
    });

    return response;
  }

  async summarizeDocument(text, options = {}) {
    try {
      const {
        maxLength = 200,
        model = 'facebook/bart-large-cnn'
      } = options;

      const response = await this.hf.summarization({
        model,
        inputs: text.substring(0, 1024), // Limit input length
        parameters: {
          max_length: maxLength,
          min_length: 50,
          do_sample: false
        }
      });

      return response.summary_text;
    } catch (error) {
      logger.error('Failed to summarize document:', error);
      
      // Fallback: extract first few sentences
      const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
      return sentences.slice(0, 3).join('. ') + '.';
    }
  }

  async classifyQuery(query) {
    try {
      const categories = [
        'definition',
        'comparison',
        'summary',
        'methodology',
        'results',
        'analysis',
        'general'
      ];

      const response = await this.hf.zeroShotClassification({
        model: 'facebook/bart-large-mnli',
        inputs: query,
        parameters: {
          candidate_labels: categories
        }
      });

      return {
        category: response.labels[0],
        confidence: response.scores[0],
        allScores: response.labels.map((label, index) => ({
          category: label,
          confidence: response.scores[index]
        }))
      };
    } catch (error) {
      logger.warn('Failed to classify query:', error);
      return {
        category: 'general',
        confidence: 0.5,
        allScores: []
      };
    }
  }

  estimateTokens(text) {
    // Rough estimation: ~4 characters per token
    return Math.ceil(text.length / 4);
  }

  async checkModelAvailability(model) {
    try {
      await this.hf.textGeneration({
        model,
        inputs: 'test',
        parameters: { max_new_tokens: 1 }
      });
      return true;
    } catch (error) {
      return false;
    }
  }
}

export default new LLMService();