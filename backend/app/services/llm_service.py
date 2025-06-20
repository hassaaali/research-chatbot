import asyncio
import json
from typing import List, Dict, Any, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from loguru import logger

from app.core.config import settings

class LLMService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = settings.TEXT_GENERATION_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the LLM model"""
        if self.is_initialized:
            return
        
        try:
            logger.info(f"Loading LLM model: {self.model_name} on {self.device}")
            
            # Load model and tokenizer in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Load tokenizer
            self.tokenizer = await loop.run_in_executor(
                None,
                AutoTokenizer.from_pretrained,
                self.model_name
            )
            
            # Load model
            self.model = await loop.run_in_executor(
                None,
                self._load_model
            )
            
            self.is_initialized = True
            logger.info(f"✅ LLM model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load LLM model: {e}")
            # Fall back to a simpler model or pipeline
            await self._initialize_fallback()
    
    def _load_model(self):
        """Load the model (runs in executor)"""
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            return model
        except Exception as e:
            logger.warning(f"Failed to load full model: {e}")
            raise
    
    async def _initialize_fallback(self):
        """Initialize with a fallback pipeline"""
        try:
            logger.info("Initializing fallback text generation pipeline")
            
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                pipeline,
                "text-generation",
                "gpt2",  # Smaller fallback model
                device=0 if self.device == "cuda" else -1
            )
            
            self.is_initialized = True
            self.model_name = "gpt2"
            logger.info("✅ Fallback model initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize fallback model: {e}")
            raise
    
    async def generate_response(self, query: str, context: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using the LLM"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            options = options or {}
            max_tokens = options.get('max_tokens', 512)
            temperature = options.get('temperature', 0.7)
            
            # Build prompt
            prompt = self._build_prompt(query, context)
            
            logger.info(f"Generating response for query: {query[:100]}...")
            
            # Generate response
            if hasattr(self.model, 'generate'):  # Full model
                response = await self._generate_with_model(prompt, max_tokens, temperature)
            else:  # Pipeline
                response = await self._generate_with_pipeline(prompt, max_tokens, temperature)
            
            # Clean and format response
            cleaned_response = self._clean_response(response, prompt)
            
            return {
                'response': cleaned_response,
                'model': self.model_name,
                'tokens_used': self._estimate_tokens(prompt + cleaned_response),
                'context_used': len(context)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return self._generate_fallback_response(query, context)
    
    async def _generate_with_model(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using full model"""
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.to("cuda")
            
            # Generate
            loop = asyncio.get_event_loop()
            with torch.no_grad():
                outputs = await loop.run_in_executor(
                    None,
                    self._model_generate,
                    inputs,
                    max_tokens,
                    temperature
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
            
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            raise
    
    def _model_generate(self, inputs, max_tokens, temperature):
        """Model generation (runs in executor)"""
        return self.model.generate(
            inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            pad_token_id=self.tokenizer.eos_token_id
        )
    
    async def _generate_with_pipeline(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using pipeline"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.model,
                prompt,
                {
                    'max_new_tokens': max_tokens,
                    'temperature': temperature,
                    'do_sample': True,
                    'top_p': 0.9,
                    'return_full_text': False
                }
            )
            
            return result[0]['generated_text']
            
        except Exception as e:
            logger.error(f"Pipeline generation failed: {e}")
            raise
    
    def _build_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Build prompt for the LLM"""
        # Format context
        context_text = ""
        for i, item in enumerate(context[:5], 1):  # Limit to top 5 contexts
            text = item.get('text', '')[:500]  # Limit context length
            doc_id = item.get('document_id', 'Unknown')
            context_text += f"[{i}] From {doc_id}: {text}\n\n"
        
        # Build prompt
        prompt = f"""You are a research assistant helping users understand academic papers. Use the provided context to answer questions accurately and comprehensively.

Context from research papers:
{context_text}

Question: {query}

Instructions:
- Provide a detailed, accurate answer based on the context
- Include specific references using [1], [2], etc. when citing sources
- If the context doesn't contain enough information, say so clearly
- Use clear, academic language but keep it accessible
- Focus on the most relevant information

Answer:"""
        
        return prompt
    
    def _clean_response(self, response: str, prompt: str) -> str:
        """Clean and format the generated response"""
        # Remove the prompt from response if it's included
        if prompt in response:
            response = response.replace(prompt, "").strip()
        
        # Remove common prefixes
        prefixes_to_remove = ["Answer:", "Response:", "A:", "Based on the context,"]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Clean up formatting
        response = response.replace('\n\n\n', '\n\n')
        response = response.strip()
        
        return response
    
    def _generate_fallback_response(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a fallback response when LLM fails"""
        if not context:
            response = "I don't have enough information in the uploaded documents to answer your question. Please make sure you've uploaded relevant research papers."
        else:
            # Simple extractive response
            response = "Based on the research papers, here's what I found:\n\n"
            for i, item in enumerate(context[:3], 1):
                text = item.get('text', '')[:200]
                response += f"{text}... [{i}]\n\n"
        
        return {
            'response': response,
            'model': 'fallback',
            'tokens_used': 0,
            'context_used': len(context),
            'error': 'LLM generation failed, using fallback'
        }
    
    async def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify the type of query"""
        try:
            # Simple rule-based classification
            query_lower = query.lower()
            
            categories = {
                'definition': ['what is', 'define', 'definition', 'meaning', 'explain'],
                'comparison': ['compare', 'difference', 'versus', 'vs', 'similar', 'different'],
                'summary': ['summarize', 'summary', 'overview', 'main points', 'key findings'],
                'methodology': ['methodology', 'method', 'approach', 'procedure', 'how'],
                'results': ['results', 'findings', 'outcomes', 'conclusions'],
                'analysis': ['analyze', 'analysis', 'evaluate', 'assessment']
            }
            
            scores = {}
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > 0:
                    scores[category] = score / len(keywords)
            
            if scores:
                best_category = max(scores, key=scores.get)
                confidence = scores[best_category]
            else:
                best_category = 'general'
                confidence = 0.5
            
            return {
                'category': best_category,
                'confidence': confidence,
                'all_scores': scores
            }
            
        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            return {
                'category': 'general',
                'confidence': 0.5,
                'all_scores': {}
            }
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'is_initialized': self.is_initialized,
            'model_type': type(self.model).__name__ if self.model else None
        }

# Global instance
llm_service = LLMService()