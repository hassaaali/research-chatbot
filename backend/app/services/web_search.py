import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from loguru import logger

from app.core.config import settings

class WebSearchService:
    def __init__(self):
        self.search_engine = settings.SEARCH_ENGINE
        self.max_results = settings.MAX_SEARCH_RESULTS
        self.google_api_key = settings.GOOGLE_API_KEY
        self.google_cse_id = settings.GOOGLE_CSE_ID
    
    async def search(self, query: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search the web for additional context"""
        if not settings.ENABLE_WEB_SEARCH:
            return []
        
        options = options or {}
        num_results = options.get('num_results', self.max_results)
        academic_only = options.get('academic_only', True)
        
        try:
            logger.info(f"Searching web for: {query[:100]}...")
            
            if self.search_engine == "google" and self.google_api_key and self.google_cse_id:
                results = await self._search_google(query, num_results, academic_only)
            else:
                results = await self._search_duckduckgo(query, num_results, academic_only)
            
            # Extract content from results
            enriched_results = await self._enrich_results(results)
            
            logger.info(f"Found {len(enriched_results)} web search results")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    async def _search_google(self, query: str, num_results: int, academic_only: bool) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        try:
            # Modify query for academic sources if requested
            if academic_only:
                query += " site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov OR site:researchgate.net"
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': min(num_results, 10)  # Google API limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        return [
                            {
                                'title': item.get('title', ''),
                                'url': item.get('link', ''),
                                'snippet': item.get('snippet', ''),
                                'source': 'google'
                            }
                            for item in items
                        ]
                    else:
                        logger.warning(f"Google search failed with status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, num_results: int, academic_only: bool) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        try:
            # Modify query for academic sources if requested
            if academic_only:
                query += " site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov OR site:researchgate.net"
            
            # Run DuckDuckGo search in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._ddg_search,
                query,
                num_results
            )
            
            return [
                {
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                    'source': 'duckduckgo'
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _ddg_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """DuckDuckGo search (runs in executor)"""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=num_results))
    
    async def _enrich_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract content from search results"""
        enriched = []
        
        for result in results:
            try:
                # Extract content from the page
                content = await self._extract_content(result['url'])
                
                enriched_result = {
                    **result,
                    'content': content,
                    'content_length': len(content),
                    'relevance_score': self._calculate_relevance(result)
                }
                
                enriched.append(enriched_result)
                
            except Exception as e:
                logger.warning(f"Failed to extract content from {result['url']}: {e}")
                # Keep result without content
                enriched.append({
                    **result,
                    'content': result.get('snippet', ''),
                    'content_length': len(result.get('snippet', '')),
                    'relevance_score': 0.5
                })
        
        # Sort by relevance
        enriched.sort(key=lambda x: x['relevance_score'], reverse=True)
        return enriched
    
    async def _extract_content(self, url: str, max_length: int = 1000) -> str:
        """Extract text content from a web page"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'}
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse HTML and extract text
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        # Limit length
                        return text[:max_length] + "..." if len(text) > max_length else text
                    else:
                        return ""
                        
        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
            return ""
    
    def _calculate_relevance(self, result: Dict[str, Any]) -> float:
        """Calculate relevance score for a search result"""
        score = 0.5  # Base score
        
        # Boost academic sources
        academic_domains = ['scholar.google.com', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'researchgate.net']
        if any(domain in result['url'] for domain in academic_domains):
            score += 0.3
        
        # Boost based on title and snippet quality
        title_length = len(result.get('title', ''))
        snippet_length = len(result.get('snippet', ''))
        
        if title_length > 20:
            score += 0.1
        if snippet_length > 50:
            score += 0.1
        
        return min(score, 1.0)
    
    async def search_academic_only(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """Search only academic sources"""
        return await self.search(
            query,
            {
                'num_results': num_results or self.max_results,
                'academic_only': True
            }
        )

# Global instance
web_search_service = WebSearchService()