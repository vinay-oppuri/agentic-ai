# agents/tech_paper_miner.py
"""
TechPaperMiner Agent
--------------------
(Hybrid "Smart Collector") Agent that finds and returns technical papers.
Returns BOTH a final JSON summary AND the raw documents for RAG.

- Fetches data from:
    • arXiv API (for pre-prints and papers)
    • Tavily Search (for blogs, news, and other papers)
    • Web Scraper (to get text from non-arXiv links)
- Uses Gemini (Native SDK) to plan collection AND summarize.
"""

import json
import asyncio
import arxiv
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

class PaperItem(BaseModel):
    """Details of a single research paper."""
    title: str = Field(..., description="The full title of the paper.")
    authors: List[str] = Field(..., description="A list of the primary authors' names.")
    summary: str = Field(..., description="The paper's abstract or a concise summary.")
    source_url: str = Field(..., description="The URL to the paper's abstract page or PDF.")
    key_findings: List[str] = Field(..., description="A 2-3 bullet point list of the paper's key findings.")

class PaperList(BaseModel):
    """A list of relevant technical papers. This is the REQUIRED format for the final summary."""
    papers: List[PaperItem]


# ----------------------------------------------------------
# Tech Paper Miner Agent (Native Implementation)
# ----------------------------------------------------------

class TechPaperMinerAgent:
    def __init__(self):
        self.client = GenAIClient._make_client(api_key=settings.google_key_paper)
        self.model_name = settings.gemini_model

    def _arxiv_search(self, query: str, max_results: int = 3) -> str:
        """Search the arXiv pre-print server for technical papers."""
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "summary": result.summary,
                    "authors": [author.name for author in result.authors],
                    "pdf_url": result.pdf_url,
                    "published_date": str(result.published.date())
                })
            
            return json.dumps(papers, indent=2)
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
            return f"arXiv search failed: {e}"

    async def _tavily_search(self, query: str, num_results: int = 5) -> str:
        """Search the web for research blogs, news, and non-arXiv papers."""
        try:
            results = await web_search(query, num_results)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return f"Tavily search failed: {e}"

    async def _scrape_website(self, url: str) -> str:
        """Smarter HTML scraper that extracts clean text from a URL."""
        try:
            return await scrape_url(url, max_chars=8000)
        except Exception as e:
            return f"Failed to scrape {url}: {e}"

    def _parse_results_to_documents(self, tool_name: str, tool_args: dict, tool_result_string: str) -> List[Document]:
        """Converts the raw JSON/text output from tools into a list of Document objects."""
        documents = []
        try:
            if tool_name == "arxiv_search":
                papers = json.loads(tool_result_string)
                if isinstance(papers, list):
                    for paper in papers:
                        content = f"Title: {paper.get('title', '')}\nAuthors: {', '.join(paper.get('authors', []))}\nSummary: {paper.get('summary', '')}"
                        metadata = {
                            "source": paper.get('pdf_url', ''),
                            "title": paper.get('title', ''),
                            "authors": paper.get('authors', []),
                            "published_date": paper.get('published_date', ''),
                            "data_source": "arXiv",
                            "query": tool_args.get("query", "")
                        }
                        documents.append(Document(page_content=content, metadata=metadata))
            
            elif tool_name == "tavily_search":
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
        """Executes paper research and returns BOTH summary and raw docs."""
        
        research_task_description = task.get("description") or task.get("topic") or state.get("intent", {}).get("idea", "latest AI research")
        logger.info(f"🔬 [TechPaperMiner] Mining for: {research_task_description}")

        try:
            collected_documents = []

            # PHASE 1: BROAD DISCOVERY (Tavily)
            logger.info("🌍 [TechPaperMiner] Phase 1: Broad Discovery (Tavily)")
            tavily_query = f"latest research papers and technical blogs about {research_task_description}"
            tavily_results_json = await self._tavily_search(tavily_query)
            collected_documents.extend(
                self._parse_results_to_documents("tavily_search", {"query": tavily_query}, tavily_results_json)
            )

            # PHASE 2: ACADEMIC SEARCH (arXiv)
            logger.info("📚 [TechPaperMiner] Phase 2: Academic Search (arXiv)")
            arxiv_query = research_task_description[:300] # arXiv query length limit safety
            arxiv_results_json = self._arxiv_search(arxiv_query)
            collected_documents.extend(
                self._parse_results_to_documents("arxiv_search", {"query": arxiv_query}, arxiv_results_json)
            )

            # PHASE 3: SCRAPE DETAILS (from Tavily results)
            logger.info("🕷️ [TechPaperMiner] Phase 3: Scrape Details")
            urls_to_scrape = []
            try:
                tavily_data = json.loads(tavily_results_json)
                if isinstance(tavily_data, list):
                    for item in tavily_data[:2]: # Limit to top 2 non-PDF links
                        url = item.get("url", "")
                        if url and not url.endswith(".pdf"):
                            urls_to_scrape.append(url)
            except Exception:
                pass

            if urls_to_scrape:
                scrape_tasks = [self._scrape_website(url) for url in urls_to_scrape]
                scrape_results = await asyncio.gather(*scrape_tasks)
                for url, res in zip(urls_to_scrape, scrape_results):
                    collected_documents.extend(
                        self._parse_results_to_documents("scrape_website", {"url": url}, res)
                    )

            # PHASE 4: SUMMARIZE (LLM)
            logger.info("📝 [TechPaperMiner] Phase 4: Summarize")
            
            context_text = ""
            for doc in collected_documents:
                context_text += f"Source: {doc.metadata.get('source')}\nTitle: {doc.metadata.get('title')}\nContent: {doc.page_content[:1500]}\n\n"

            prompt = f"""
            You are an AI research assistant. Your goal is to find key technical papers, articles, and libraries related to:
            "{research_task_description}"

            RESEARCH DATA:
            {context_text}

            Analyze the abstracts, snippets, and scraped text.
            Select the most important 3-5 papers/articles/libraries.
            Return the result as a JSON object matching the `PaperList` schema.
            """

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PaperList,
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )

            final_json = response.parsed
            
            if not final_json:
                 try:
                     final_json = PaperList.model_validate_json(response.text)
                 except:
                     logger.error("Failed to parse PaperList from LLM response")
                     return {"success": False, "error": "Failed to parse LLM response"}

            final_summary_list = [paper.model_dump() for paper in final_json.papers]

            return {
                "success": True,
                "output_summary": final_summary_list,
                "output_raw_docs": [d.dict() if hasattr(d, 'dict') else d for d in collected_documents],
                "output_type": "PaperReport",
                "meta": {"source": "GenAI+Native", "agent": "TechPaperMiner"},
            }

        except Exception as e:
            logger.exception("TechPaperMinerAgent failed.")
            return {"success": False, "error": str(e)}


# Wrapper function to maintain interface with graph
async def tech_paper_miner_agent(query: str) -> Dict[str, Any]:
    agent = TechPaperMinerAgent()
    task = {"description": query}
    state = {"intent": {"idea": query}}
    return await agent.run(task, state)
