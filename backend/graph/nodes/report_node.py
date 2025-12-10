# graph/nodes/report_node.py
import json
from typing import List, Dict, Any

from loguru import logger

from graph.state import AgentState
from core.llm import llm_generate
from core.summarizer import summarize_docs
from core.types import Document


async def report_node(state: AgentState) -> AgentState:
    """
    Final node:
      - Builds Markdown report from intent, agent outputs, and RAG docs
      - Produces a shorter summary
    """
    user_input = state["user_input"]
    intent = state.get("intent", {})
    agent_outputs: List[Dict[str, Any]] = state.get("agent_outputs", [])
    docs: List[Document] = state.get("retrieved_docs", [])

    logger.info("[ReportNode] Building final report...")

    # Compact versions of data for prompt
    intent_json = json.dumps(intent, ensure_ascii=False, indent=2)
    agent_json = json.dumps(agent_outputs, ensure_ascii=False, indent=2)

    doc_snippets = []
    for d in docs[:5]:
        doc_snippets.append(
            {
                "content": d.page_content[:800],
                "metadata": d.metadata,
            }
        )
    docs_json = json.dumps(doc_snippets, ensure_ascii=False, indent=2)

    prompt = f"""
You are an AI Strategy Consultant.

The user has the following startup idea / query:

\"\"\"{user_input}\"\"\"

We have the following:

[1] Parsed intent (JSON):
{intent_json}

[2] Agent research results (JSON):
{agent_json}

[3] Retrieved context snippets (from vector search):
{docs_json}

Write a **detailed, structured startup strategy report** in Markdown,
with sections:

# Title
## Executive Summary
## Market & Trends
## Competitor Landscape
## Technology & Implementation Insights
## Risks & Challenges
## Strategic Recommendations
## Possible Next Experiments

Be specific, actionable, and concise. Use bullet points where helpful.
"""

    final_report = await llm_generate(prompt, temperature=0.35)

    # Shorter summary:
    try:
        summary = await summarize_docs(docs) if docs else final_report[:400]
    except Exception:
        summary = final_report[:400]

    logger.info("[ReportNode] Report + summary generated.")

    return {
        **state,
        "final_report": final_report,
        "summary": summary,
    }
