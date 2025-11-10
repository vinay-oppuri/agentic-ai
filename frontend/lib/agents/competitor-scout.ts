import { chatWithLLM } from "../llm";

export async function competitorScout(idea: string) {
  try {
    const prompt = `
      You are a startup analyst with access to global startup knowledge.
      Analyze the startup idea: "${idea}".
      
      Steps:
      1. List 3-5 competitors (realistic or known) for this idea.
      2. Compare their strengths and weaknesses.
      3. Identify gaps or opportunities the new startup could exploit.
      
      Return structured JSON:
      {
        "keyPlayers": [
          { "name": "...", "funding": "...", "region": "...", "focus": "..." }
        ],
        "strengthsWeaknesses": "...",
        "opportunityGap": "..."
      }
    `;

    const response = await chatWithLLM(prompt, []);

    // Try to parse JSON if the LLM returned JSON. Otherwise return raw text.
    if (typeof response === "string") {
      try {
        const parsed = JSON.parse(response);
        return parsed;
      } catch {
        // best-effort: try to find a JSON block in the response
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            return JSON.parse(jsonMatch[0]);
          } catch {
            // Fall through
          }
        }
        return { rawResponse: response };
      }
    }

    // If chatWithLLM returned an object already
    return response;
  } catch (error) {
    console.error("Competitor Error:", error);
    return { error: "Failed to generate competitor analysis" };
  }
}