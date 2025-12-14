# agents/trend_scraper.py
"""
TrendScraper Agent
------------------
(Hybrid "Smart Collector") Agent that discovers trends and returns BOTH a summary and raw documents.

- Fetches data from:
    • News API (general headlines)
    • Reddit (developer/startup discussions)
    • Tavily Search (fallback)
- Uses Gemini (Native SDK) to adaptively plan collection AND summarize.
"""

import json
import asyncio
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from google.genai import types
from infra.genai_client import GenAIClient
from app.config import settings
from core.utils import web_search
from core.types import Document


# ----------------------------------------------------------
# Output Structure for Trends
# ----------------------------------------------------------

class TrendItem(BaseModel):
    trend_name: str = Field(..., description="Name of the emerging trend, pain point, or developer need.")
    short_summary: str = Field(..., description="Brief summary of the trend, including who it affects (e.g., developers, tech leads).")
    relevance_score: int = Field(..., description="Relevance score to the user's task (0–100)")
    supporting_sources: List[str] = Field(..., description="List of supporting source URLs")

class TrendList(BaseModel):
    """A list of current trends. This is the REQUIRED format for the final summary."""
    trends: List[TrendItem]


# ----------------------------------------------------------
# Trends Scraper Agent (Native Implementation)
# ----------------------------------------------------------

class TrendsScraperAgent:
    def __init__(self):
        self.client = GenAIClient._make_client(api_key=settings.google_key_trend)
        self.model_name = settings.gemini_model

    def _fetch_trending_news(self, topic: str = "technology", num_results: int = 10) -> str:
        """Fetch latest news articles using NewsAPI."""
        api_key = settings.news_api_key
        if not api_key:
            return "News API key not configured."

        try:
            url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize={num_results}&language=en&apiKey={api_key}"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            return json.dumps(data.get("articles", []), indent=2)
        except Exception as e:
            logger.warning(f"News API failed: {e}")
            return f"News API failed: {e}"

    def _fetch_reddit_trends(self, subreddit: str, limit: int = 5) -> str:
        """Fetch top Reddit posts from a specific, relevant subreddit."""
        try:
            logger.info(f"Attempting to fetch from subreddit: r/{subreddit}")
            headers = {"User-Agent": "python:agentic-ai-researcher:v1.0 (by /u/agentic_ai)"}
            url = f"https://www.reddit.com/r/{subreddit}/top/.json?limit={limit}&t=day"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            posts = [
                {
                    "title": post["data"]["title"],
                    "score": post["data"]["score"],
                    "url": f"https://reddit.com{post['data']['permalink']}"
                }
                for post in data["data"]["children"]
            ]
            return json.dumps(posts, indent=2)
        except Exception as e:
            logger.warning(f"Reddit fetch failed for r/{subreddit}: {e}")
            return f"Reddit fetch failed for r/{subreddit}: {e}"

    async def _tavily_trend_search(self, query: str, num_results: int = 5) -> str:
        """Web search to discover broad trends or 'drill down' on specific new topics."""
        try:
            results = await web_search(query, num_results)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.warning(f"Tavily trend search failed: {e}")
            return f"Tavily trend search failed: {e}"

    def _parse_results_to_documents(self, tool_name: str, tool_args: dict, tool_result_string: str) -> List[Document]:
        """Converts the raw JSON output from tools into a list of Document objects."""
        documents = []
        try:
            data = json.loads(tool_result_string)
            if not isinstance(data, list):
                return []

            if tool_name == "NewsAPITool":
                for article in data:
                    content = f"Title: {article.get('title', '')}\nDescription: {article.get('description', '')}"
                    metadata = {
                        "source": article.get('url', ''),
                        "title": article.get('title', ''),
                        "published_at": article.get('publishedAt', ''),
                        "data_source": "NewsAPI",
                        "query": tool_args.get("topic", "")
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
            
            elif tool_name == "RedditTrendTool":
                for post in data:
                    content = post.get('title', '')
                    metadata = {
                        "source": post.get('url', ''),
                        "title": post.get('title', ''),
                        "score": post.get('score', 0),
                        "data_source": "Reddit",
                        "subreddit": tool_args.get("subreddit", "")
                    }
                    documents.append(Document(page_content=content, metadata=metadata))

            elif tool_name == "TavilyTrendSearch":
                for result in data:
                    content = result.get('content', '')
                    metadata = {
                        "source": result.get('url', ''),
                        "title": result.get('title', ''),
                        "score": result.get('score', 0),
                        "data_source": "Tavily",
                        "query": tool_args.get("query", "")
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
        
        except Exception as e:
            logger.warning(f"Failed to parse JSON for {tool_name}: {e}")
        
        return documents

    async def run(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes trend analysis and returns BOTH summary and raw docs."""
        
        research_task_description = task.get("description") or task.get("topic") or state.get("intent", {}).get("idea", "technology")
        logger.info(f"🌍 [TrendScraper] Gathering trends for: {research_task_description}")

        try:
            collected_documents = []

            # PHASE 1: BROAD SEARCH & SURVEYS
            logger.info("📡 [TrendScraper] Phase 1: Broad Search & News")
            
            # Tavily for surveys/reports
            tavily_query = f"developer surveys and trends 2025 for {research_task_description}"
            tavily_results = await self._tavily_trend_search(tavily_query)
            collected_documents.extend(
                self._parse_results_to_documents("TavilyTrendSearch", {"query": tavily_query}, tavily_results)
            )

            # NewsAPI
            news_results = self._fetch_trending_news(topic=research_task_description, num_results=5)
            collected_documents.extend(
                self._parse_results_to_documents("NewsAPITool", {"topic": research_task_description}, news_results)
            )

            # PHASE 2: DEEP DIVE (Tavily)
            # Simple heuristic: drill down on "pain points"
            logger.info("🔍 [TrendScraper] Phase 2: Deep Dive")
            drill_down_query = f"major developer pain points and challenges in {research_task_description}"
            drill_down_results = await self._tavily_trend_search(drill_down_query)
            collected_documents.extend(
                self._parse_results_to_documents("TavilyTrendSearch", {"query": drill_down_query}, drill_down_results)
            )

            # PHASE 3: COMMUNITY PULSE (Reddit)
            # Heuristic: pick a subreddit based on keywords or default to 'programming'
            subreddit = "programming"
            if "ai" in research_task_description.lower():
                subreddit = "ArtificialInteligence"
            elif "web" in research_task_description.lower():
                subreddit = "webdev"
            elif "security" in research_task_description.lower():
                subreddit = "netsec"
            
            logger.info(f"💬 [TrendScraper] Phase 3: Community Pulse (r/{subreddit})")
            reddit_results = self._fetch_reddit_trends(subreddit=subreddit)
            collected_documents.extend(
                self._parse_results_to_documents("RedditTrendTool", {"subreddit": subreddit}, reddit_results)
            )

            # PHASE 4: SUMMARIZE (LLM)
            logger.info("📝 [TrendScraper] Phase 4: Summarize")
            
            context_text = ""
            for doc in collected_documents:
                context_text += f"Source: {doc.metadata.get('source')}\nTitle: {doc.metadata.get('title')}\nContent: {doc.page_content[:1000]}\n\n"

            prompt = f"""
            You are an AI research analyst. Your goal is to find trends on:
            "{research_task_description}"

            TREND DATA:
            {context_text}

            Analyze the data. Identify 3-5 key trends, needs, or pain points.
            Return the result as a JSON object matching the `TrendList` schema.
            """

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TrendList,
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )

            final_json = response.parsed
            
            if not final_json:
                 try:
                     final_json = TrendList.model_validate_json(response.text)
                 except:
                     logger.error("Failed to parse TrendList from LLM response")
                     return {"success": False, "error": "Failed to parse LLM response"}

            summary_list = [trend.model_dump() for trend in final_json.trends]

            return {
                "success": True,
                "output_summary": summary_list,
                "output_raw_docs": [d.dict() if hasattr(d, 'dict') else d for d in collected_documents],
                "output_type": "TrendReport",
                "meta": {"source": "GenAI+Native", "agent": "TrendsScraper"},
            }

        except Exception as e:
            logger.exception("TrendsScraperAgent failed.")
            return {"success": False, "error": str(e)}


# Wrapper function to maintain interface with graph
async def trend_scraper_agent(query: str) -> Dict[str, Any]:
    agent = TrendsScraperAgent()
    task = {"description": query}
    state = {"intent": {"idea": query}}
    return await agent.run(task, state)
