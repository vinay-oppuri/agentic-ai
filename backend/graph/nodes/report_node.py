# graph/nodes/report_node.py
"""
Report Node
-----------
Final step in the pipeline.
Synthesizes all gathered information into a comprehensive Markdown report.
"""

import json
from typing import Any, Dict, List

from loguru import logger

from graph.state import AgentState
from core.llm import llm_generate
from core.summarizer import summarize_docs
from core.types import Document
from app.config import settings


async def report_node(state: AgentState) -> AgentState:
    """
    Generates the final strategy report.
    """
    user_input = state["user_input"]
    intent = state.get("intent", {})
    agent_outputs = state.get("agent_outputs", [])
    docs = state.get("retrieved_docs", [])

    logger.info("📝 [ReportNode] Drafting final report...")

    # Prepare Context
    intent_json = json.dumps(intent, ensure_ascii=False, indent=2)
    
    # Simplify agent outputs for prompt context
    simplified_outputs = []
    for item in agent_outputs:
        # Handle both list of dicts (new agents) and other formats
        summary_data = item.get("output_summary") or item.get("result")
        simplified_outputs.append({
            "agent": item.get("agent") or item.get("meta", {}).get("agent"),
            "summary": summary_data
        })
    agent_json = json.dumps(simplified_outputs, ensure_ascii=False, indent=2)

    # Prepare RAG snippets
    doc_snippets = []
    for d in docs[:8]: # Increased context
        doc_snippets.append({
            "content": d.page_content[:1500], 
            "metadata": d.metadata,
        })
    docs_json = json.dumps(doc_snippets, ensure_ascii=False, indent=2)

    prompt = f"""
    You are an expert **Startup Strategy Consultant** and **Product Analyst**.
    
    Your goal is to write a comprehensive, actionable, and professional strategy report for the following startup idea:
    
    # STARTUP IDEA
    "{user_input}"
    
    # CONTEXT & RESEARCH
    
    ## 1. Parsed Intent
    {intent_json}
    
    ## 2. Agent Research Findings (Competitors, Trends, Papers)
    {agent_json}
    
    ## 3. Retrieved Knowledge (RAG)
    {docs_json}
    
    # INSTRUCTIONS
    
    Write a detailed **Markdown** report. Do not use JSON. Use clear headings, bullet points, and bold text for emphasis.
    
    The report MUST include the following sections:
    
    # 1. Executive Summary
    (A concise 3-4 sentence overview of the opportunity and verdict.)
    
    # 2. Market Analysis & Trends
    (Analyze the market size, growth trends, and "Why Now?". Cite specific trends found by the agents.)
    
    # 3. Competitor Landscape
    (Compare key competitors. Highlight their strengths/weaknesses and identify the "Blue Ocean" opportunity for this startup.)
    
    # 4. Technical Feasibility & Research
    (Discuss relevant papers, libraries, and technical challenges. How can the tech be implemented?)
    
    # 5. Strategic Recommendations
    (Provide 3-5 high-impact recommendations for MVP features, go-to-market strategy, or differentiation.)
    
    # 6. Risks & Mitigations
    (Honest assessment of risks (market, tech, legal) and how to mitigate them.)
    
    # 7. Roadmap (Next 6 Months)
    (A high-level timeline: Month 1-2, Month 3-4, Month 5-6.)
    
    ---
    
    **Tone:** Professional, objective, encouraging but realistic.
    **Format:** Clean Markdown.
    """

    try:
        final_report = await llm_generate(prompt, temperature=0.4, model="gemini-2.5-flash", max_tokens=4096, api_key=settings.google_key_report)
    except Exception as e:
        logger.error(f"❌ [ReportNode] Report generation failed: {e}")
        final_report = f"# Error Generating Report\n\n{e}"

    # Generate a short summary for the UI
    try:
        if docs:
            summary = await summarize_docs(docs)
        else:
            summary = final_report[:500] + "..."
    except Exception:
        summary = "Summary generation failed."

    logger.info("✅ [ReportNode] Report generated.")

    return {
        **state,
        "final_report": final_report,
        "summary": summary,
    }
