# core/intent_parser.py
"""
Intent Parser Module
--------------------
Analyzes user input to extract structured metadata about the startup idea.
Uses Google GenAI for deep analysis, falling back to rule-based heuristics
if the LLM is unavailable or fails.
"""

import re
import json
from typing import Any, Dict, List, Optional

from loguru import logger
from google import genai
from app.config import settings


class IntentParser:
    """
    Parses user queries into structured intent metadata.
    """

    # Heuristic Data
    DOMAINS = [
        "health", "education", "finance", "travel", "food",
        "fitness", "pet", "real estate", "transportation",
        "ai", "mental health", "agriculture", "gaming",
        "retail", "sustainability"
    ]

    TECH_TERMS = [
        "ai", "machine learning", "blockchain", "nlp", "data analytics",
        "ar", "vr", "iot", "chatbot", "llm", "neural network"
    ]

    INTENT_PATTERNS = {
        "compare": r"(compare|vs|difference|better than)",
        "trend": r"(trend|market|growth|statistics)",
        "tech": r"(technology|innovation|research|paper)",
        "idea": r"(idea|startup|launch|build)"
    }

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.client = None
        if use_llm and (settings.google_key_planner or settings.google_api_key):
             self.client = genai.Client(api_key=settings.google_key_planner or settings.google_api_key)

    async def parse(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point for parsing intent.
        
        Args:
            user_input (str): The user's query string.
            
        Returns:
            Dict[str, Any]: Structured metadata.
        """
        logger.info(f"🔍 Parsing intent: {user_input}")

        if self.use_llm and self.client:
            try:
                return await self._parse_with_llm(user_input)
            except Exception as e:
                logger.warning(f"⚠️ LLM parsing failed ({e}), falling back to regex rules.")

        return self._parse_with_rules(user_input)

    async def _parse_with_llm(self, query: str) -> Dict[str, Any]:
        """Uses Gemini to extract intent."""
        prompt = f"""
        You are an expert intent parser for a startup research assistant.
        Analyze the following user query and extract structured intent.
        
        USER QUERY: "{query}"
        
        Return a JSON object with the following schema:
        {{
            "industry": "string (e.g., AI, SaaS, E-commerce)",
            "target_audience": "string",
            "problem_statement": "string",
            "intent_type": "string (one of: market_research, competitor_analysis, trend_analysis, technical_research)",
            "complexity_level": "string (low, medium, high)",
            "agent_triggers": ["list of agents to trigger (competitor_scout, trend_scraper, tech_paper_miner)"]
        }}
        """

        try:
            # We need to import llm_generate here or use the client directly
            # Since this class has self.client, let's use it directly but with the specific key
            # However, self.client is already initialized with the specific key in __init__
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    max_output_tokens=1024,
                    temperature=0.1
                )
            )
            
            text = response.text
            parsed = self._safe_extract_json(text)
            parsed["raw_query"] = query
            
            logger.success("✅ LLM intent parsed successfully.")
            return parsed
            
        except Exception as e:
            logger.warning(f"⚠️ LLM parsing failed ({e}), falling back to regex rules.")
            return self._parse_with_rules(query)

    def _parse_with_rules(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based parser."""
        logger.info("🧩 Using rule-based parser")

        text_lower = text.lower()
        
        # Extract fields using heuristics
        industry = next((d for d in self.DOMAINS if d in text_lower), "general")
        tech = [t for t in self.TECH_TERMS if t.lower() in text_lower]
        
        intent_type = "idea"
        for name, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, text_lower):
                intent_type = name
                break

        # Naive competitor extraction (Capitalized words)
        # This is very rough, but better than nothing for a fallback
        competitors = re.findall(r"[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?", text)
        # Filter out common starting words if they appear at start of sentence (heuristic)
        competitors = [c for c in competitors if len(c) > 3] 

        parsed = {
            "industry": industry,
            "business_model": self._infer_business_model(text_lower),
            "target_audience": self._infer_audience(text_lower),
            "tech_keywords": tech,
            "competitor_names": competitors,
            "intent_type": intent_type,
            "problem_statement": text,
            "solution_summary": "",
            "data_needs": [],
            "agent_triggers": ["trend_scraper", "competitor_scout", "tech_paper_miner"],
            "complexity_level": "medium",
            "raw_query": text
        }

        logger.success("✅ Rule-based intent parsed.")
        return parsed

    def _infer_business_model(self, text: str) -> str:
        if "platform" in text: return "Platform"
        if "app" in text: return "Mobile App"
        if "service" in text: return "Service"
        if "tool" in text or "software" in text: return "SaaS"
        if "marketplace" in text: return "Marketplace"
        return "General"

    def _infer_audience(self, text: str) -> str:
        if "student" in text: return "Students"
        if "developer" in text or "engineer" in text: return "Developers"
        if "business" in text or "startup" in text: return "Businesses"
        if "doctor" in text or "patient" in text: return "Healthcare Users"
        return "General Audience"

    def _safe_extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts JSON from LLM output, handling markdown fences."""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {
            "industry": None,
            "business_model": None,
            "target_audience": None,
            "tech_keywords": [],
            "competitor_names": [],
            "intent_type": "idea",
        }


if __name__ == "__main__":
    # CLI Test
    parser = IntentParser()
    q = "GitHub repository analysis tool for developers"
    print(json.dumps(parser.parse(q), indent=2))