# agents/competitor_scout.py
"""
CompetitorScout Agent
---------------------
(Hybrid) CompetitorScout
Returns BOTH a final JSON summary AND the raw documents for RAG.
- Gemini (Native SDK)
- Tavily Search
- Web Scraping
- Manual Agent Loop
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from google.genai import types
from infra.genai_client import GenAIClient
from app.config import settings
from core.utils import scrape_url, web_search
from core.types import Document


# ----------------------------------------------------------
# Define the Structured Output Shape
# ----------------------------------------------------------

class Competitor(BaseModel):
    """A single competitor's details."""
    name: str = Field(..., description="The name of the competitor company.")
    domain: str = Field(..., description="The market or domain they operate in (e.g., 'Code Security').")
    summary: str = Field(..., description="A brief summary of what the competitor does.")
    website: Optional[str] = Field(None, description="The competitor's main website URL.")
    reason_for_similarity: str = Field(..., description="Why this company is a competitor to the user's idea.")
    estimated_similarity_score: int = Field(..., description="A 0-100 score of how similar they are.", ge=0, le=100)
    
    key_features: Optional[List[str]] = Field(
        None, description="A list of key features or product offerings."
    )
    pricing_model: Optional[str] = Field(
        None, description="The competitor's pricing model (e.g., 'Freemium', 'Enterprise', 'Open Source')."
    )
    target_audience: Optional[str] = Field(
        None, description="The primary target audience (e.g., 'Hobbyist Developers', 'Enterprise DevOps Teams')."
    )

class CompetitorList(BaseModel):
    """A list of competitors. This is the REQUIRED format for the final answer."""
    competitors: List[Competitor]


# ----------------------------------------------------------
# Competitor Scout (Native Implementation)
# ----------------------------------------------------------

class CompetitorScoutAgent:
    def __init__(self):
        self.client = GenAIClient._make_client(api_key=settings.google_key_competitor)
        self.model_name = settings.gemini_model

    async def _tavily_search(self, query: str, num_results: int = 5) -> str:
        """Search for top competitor companies using Tavily API."""
        try:
            results = await web_search(query, num_results)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return f"Tavily search failed: {e}"

    async def _scrape_website(self, url: str) -> str:
        """Smarter HTML scraper that extracts clean text."""
        try:
            return await scrape_url(url, max_chars=8000)
        except Exception as e:
            return f"Failed to scrape {url}: {e}"

    def _parse_results_to_documents(self, tool_name: str, tool_args: dict, tool_result_string: str) -> List[Document]:
        """Converts the raw JSON/text output from tools into a list of Document objects."""
        documents = []
        try:
            if tool_name == "tavily_search":
                results = json.loads(tool_result_string)
                if isinstance(results, list):
                    for res in results:
                        content = res.get('content', '')
                        metadata = {
                            "source": res.get('url', ''),
                            "title": res.get('title', ''),
                            "data_source": "Tavily",
                            "query": tool_args.get("query", "")
                        }
                        documents.append(Document(page_content=content, metadata=metadata))
            
            elif tool_name == "scrape_website":
                url = tool_args.get("url", "")
                if not tool_result_string.startswith("Failed to scrape"):
                    content = tool_result_string
                    metadata = {
                        "source": url,
                        "title": f"Scraped content from {url}",
                        "data_source": "WebScraper"
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
        
        except Exception as e:
            logger.warning(f"Failed to parse tool result for {tool_name}: {e}")
        
        return documents

    async def run(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes competitor analysis and returns BOTH summary and raw docs."""
        try:
            description = task.get("description") or state.get("intent", {}).get("idea", "") or "competitor analysis"
            logger.info(f"🧠 [CompetitorScout] Analyzing: {description}")

            # 1. Search Phase
            search_query = f"top competitors for {description}"
            logger.info(f"🔍 [CompetitorScout] Searching: {search_query}")
            search_results_json = await self._tavily_search(search_query)
            
            collected_documents = self._parse_results_to_documents("tavily_search", {"query": search_query}, search_results_json)
            
            # 2. Scrape Phase (Select top 3 URLs from search results)
            urls_to_scrape = []
            try:
                search_data = json.loads(search_results_json)
                if isinstance(search_data, list):
                    for item in search_data[:3]: # Limit to top 3
                        if item.get("url"):
                            urls_to_scrape.append(item["url"])
            except Exception:
                pass

            logger.info(f"🕷️ [CompetitorScout] Scraping {len(urls_to_scrape)} sites...")
            scrape_tasks = [self._scrape_website(url) for url in urls_to_scrape]
            scrape_results = await asyncio.gather(*scrape_tasks)

            for url, res in zip(urls_to_scrape, scrape_results):
                collected_documents.extend(
                    self._parse_results_to_documents("scrape_website", {"url": url}, res)
                )

            # 3. Analysis Phase (LLM)
            logger.info("🤔 [CompetitorScout] Generating analysis...")
            
            # Prepare context from collected docs
            context_text = ""
            for doc in collected_documents:
                context_text += f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content[:2000]}\n\n"

            prompt = f"""
            Analyze the following competitor data for the startup idea: "{description}"

            COMPETITOR DATA:
            {context_text}

            Identify the top competitors, their key features, pricing, and why they are similar.
            Return the result as a JSON object matching the `CompetitorList` schema.
            """

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CompetitorList,
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )

            final_json = response.parsed
            
            # Handle case where parsed is None but text exists (though SDK usually handles this)
            if not final_json:
                 # Fallback parsing if needed, but SDK should handle it with response_schema
                 try:
                     final_json = CompetitorList.model_validate_json(response.text)
                 except:
                     logger.error("Failed to parse CompetitorList from LLM response")
                     return {"success": False, "error": "Failed to parse LLM response"}

            competitors_list = [comp.model_dump() for comp in final_json.competitors]

            return {
                "success": True,
                "output_summary": competitors_list,
                "output_raw_docs": [d.dict() if hasattr(d, 'dict') else d for d in collected_documents], # Ensure serializable
                "output_type": "CompetitorAnalysisReport",
                "meta": {"source": "GenAI+Native", "agent": "CompetitorScout"},
            }

        except Exception as e:
            logger.exception("CompetitorScoutAgent failed.")
            return {"success": False, "error": str(e)}


# Wrapper function to maintain interface with graph
async def competitor_scout_agent(query: str) -> Dict[str, Any]:
    agent = CompetitorScoutAgent()
    task = {"description": query}
    state = {"intent": {"idea": query}}
    return await agent.run(task, state)
