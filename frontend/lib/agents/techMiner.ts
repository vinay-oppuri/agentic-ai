import { NextResponse } from "next/server";
import { chatWithLLM } from "../llm";

export async function techMiner(idea: string) {
  try {
    const prompt = `
      You are TechMiner, an AI that extracts research insights.
      Given the idea: "${idea}", find and summarize 5 recent or relevant research papers or innovations.
      For each, return:
      - Title
      - Short summary (2-3 sentences)
      - Link (if known or relevant)
      Format the response as JSON with a "papers" array.
    `;

    const response = await chatWithLLM(prompt, []);

    // Try to safely parse Gemini's JSON-like output
    let data;
    if (!response) {
      data = { papers: [{ title: "Error", summary: "No response from LLM." }] };
    } else {
        try {
            const cleanedResponse = response.replace(/```json/g, '').replace(/```/g, '');
            data = JSON.parse(cleanedResponse);
        } catch {
            data = { papers: [{ title: "Parsing error", summary: response }] };
        }
    }

    return {
      agent: "TechMiner (Gemini)",
      idea,
      ...data,
      fetchedAt: new Date().toISOString(),
    };
  } catch (error) {
    console.error("Error using Gemini:", error);
    return NextResponse.json({ error: "Failed to fetch from Gemini." }, { status: 500 });
  }
}
