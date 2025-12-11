"""
intent_parser.py
----------------
Extracts structured intent & semantic metadata from user startup queries.
Uses Google GenAI (native API) + rule-based fallback.
"""

import re
import json
from typing import Any, Dict

from loguru import logger
from google import genai
from app.config import settings


client = genai.Client(api_key=settings.google_api_key)


class IntentParser:
    """
    Intent Parser Agent
    -------------------
    Extracts structured metadata such as:
        - industry
        - target audience
        - business model
        - tech keywords
        - competitor names
        - intent type (idea, compare, trend, tech, etc.)
        - problem & solution summary
        - data needs
        - which agents to activate
        - complexity level
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

        # Fallback rules
        self.domains = [
            "health", "education", "finance", "travel", "food",
            "fitness", "pet", "real estate", "transportation",
            "ai", "mental health", "agriculture", "gaming",
            "retail", "sustainability"
        ]

        self.tech_terms = [
            "ai", "machine learning", "blockchain", "nlp", "data analytics",
            "ar", "vr", "iot", "chatbot", "llm", "neural network"
        ]

        self.intent_patterns = {
            "compare": r"(compare|vs|difference|better than)",
            "trend": r"(trend|market|growth|statistics)",
            "tech": r"(technology|innovation|research|paper)",
            "idea": r"(idea|startup|launch|build)"
        }

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def parse(self, user_input: str) -> Dict[str, Any]:
        logger.info(f"🔍 Parsing intent: {user_input}")

        if self.use_llm:
            try:
                return self._parse_with_llm(user_input)
            except Exception as e:
                logger.warning(f"⚠️ LLM parsing failed ({e}), falling back to regex rules.")

        return self._parse_with_rules(user_input)

    # --------------------------------------------------------
    # LLM PARSER (Google GenAI)
    # --------------------------------------------------------
    def _parse_with_llm(self, query: str) -> Dict[str, Any]:
        prompt = f"""
You are a top-tier Intent Parsing AI for a Startup Research Assistant.

Analyze the user query below and extract structured metadata.

USER QUERY:
{query}

RETURN A VALID JSON OBJECT WITH EXACTLY THESE FIELDS:

{{
  "industry": "...",
  "business_model": "...",
  "target_audience": "...",
  "tech_keywords": ["..."],
  "competitor_names": ["..."],
  "intent_type": "...",
  "problem_statement": "...",
  "solution_summary": "...",
  "data_needs": ["..."],
  "agent_triggers": ["trend_scraper", "competitor_scout", "paper_miner"],
  "complexity_level": "low | medium | high"
}}

Ensure the JSON is clean and valid.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text
        parsed = self._safe_extract_json(text)
        parsed["raw_query"] = query

        logger.success("✅ LLM intent parsed successfully.")
        return parsed

    # --------------------------------------------------------
    # RULE-BASED FALLBACK PARSER
    # --------------------------------------------------------
    def _parse_with_rules(self, text: str) -> Dict[str, Any]:
        logger.info("🧩 Using rule-based parser")

        text_lower = text.lower()
        industry = next((d for d in self.domains if d in text_lower), "general")

        tech = [t for t in self.tech_terms if t.lower() in text_lower]

        intent_type = next(
            (name for name, pattern in self.intent_patterns.items()
             if re.search(pattern, text_lower)),
            "idea"
        )

        competitors = re.findall(r"[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?", text)
        competitors = competitors if len(competitors) > 1 else []

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

    # --------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------
    def _infer_business_model(self, text: str) -> str:
        if "platform" in text:
            return "Platform"
        if "app" in text:
            return "Mobile App"
        if "service" in text:
            return "Service"
        if "tool" in text or "software" in text:
            return "SaaS"
        if "marketplace" in text:
            return "Marketplace"
        return "General"

    def _infer_audience(self, text: str) -> str:
        if "student" in text:
            return "Students"
        if "developer" in text or "engineer" in text:
            return "Developers"
        if "business" in text or "startup" in text:
            return "Businesses"
        if "doctor" in text or "patient" in text:
            return "Healthcare Users"
        return "General Audience"

    def _safe_extract_json(self, text: str) -> Dict[str, Any]:
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


# --------------------------------------------------------
# Standalone CLI test
# --------------------------------------------------------
if __name__ == "__main__":
    parser = IntentParser()
    q = (
        "GitHub repository analysis tool for developers where "
        "user can give repo links and the tool will show insights about "
        "code quality, vulnerabilities, architecture, etc."
    )
    print(parser.parse(q))