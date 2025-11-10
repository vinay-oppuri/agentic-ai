import { chatWithLLM } from "../llm";

interface Paper {
  title: string;
  summary: string;
  link?: string;
}

interface Competitor {
    name: string;
    description: string;
    link?: string;
}

interface Trend {
    title: string;
    summary: string;
    link?: string;
}

export async function summarizer(data: {
  idea: string;
  competitors: Competitor[];
  tech: Paper[];
  trends: Trend[];
}) {
  const prompt = `
    You are a professional startup strategist and market analyst.

    Based on the following information, generate a structured "Startup Insight Report" in strict JSON format.

    Startup Idea:
    ${data.idea}

    Competitor Insights:
    ${JSON.stringify(data.competitors, null, 2)}

    Tech & Research Innovations:
    ${JSON.stringify(data.tech, null, 2)}

    Market & Trend Signals:
    ${JSON.stringify(data.trends, null, 2)}

    ---
    Return ONLY valid JSON with this structure (no markdown, no explanations):

    {
      "marketAnalysis": "Summarize the current market landscape, size, and opportunities.",
      "competitorAnalysis": "Summarize major competitors, their positioning, and gaps.",
      "keyInsights": "Highlight 3-5 actionable insights or recommendations."
    }
  `

  try {
    const response = await chatWithLLM(prompt, []);

    if (typeof response !== "string") {
      throw new Error("Unexpected LLM response format");
    }

    // 🧹 Clean LLM output (remove markdown, backticks, etc.)
    const cleaned = response
      .replace(/```json/gi, "")
      .replace(/```/g, "")
      .replace(/^[^{]*({[\s\S]*})[^}]*$/m, "$1") // extract JSON block if extra text is present
      .trim();

    try {
      const parsed = JSON.parse(cleaned);
      return {
        marketAnalysis: parsed.marketAnalysis || "No market analysis provided.",
        competitorAnalysis: parsed.competitorAnalysis || "No competitor analysis provided.",
        keyInsights: parsed.keyInsights || "No key insights provided.",
      };
    } catch (jsonError) {
      console.warn("⚠️ JSON parsing failed, fallback mode:", jsonError);
      return {
        marketAnalysis: extractSection(response, "Market") || response,
        competitorAnalysis: extractSection(response, "Competitor") || "N/A",
        keyInsights: extractSection(response, "Insight") || "N/A",
      };
    }
  } catch (error) {
    console.error("Error generating startup insight report:", error);
    return {
      marketAnalysis: "Could not generate market analysis.",
      competitorAnalysis: "Could not generate competitor analysis.",
      keyInsights: "Could not generate insights.",
    };
  }
}

// 🔍 Helper: Extract section heuristically from text fallback
function extractSection(text: string, keyword: string): string | null {
  const regex = new RegExp(`${keyword}[\\s\\S]*?(?=\\n\\n|$)`, "i");
  const match = text.match(regex);
  return match ? match[0].trim() : null;
}