import { orchestrateResearch } from "./agents/orchestrator";
import { chatWithLLM } from "./llm";

const MAX_MEMORY_SIZE = 10;

// This is a simple in-memory store. For production, you should use a persistent database.
const memory: { role: 'user' | 'assistant'; content: string }[] = [];

function manageMemory(newMessage: { role: 'user' | 'assistant'; content: string }) {
  memory.push(newMessage);
  if (memory.length > MAX_MEMORY_SIZE) {
    // Remove the oldest two messages (one user, one assistant) to keep the conversation history concise.
    memory.splice(0, 2);
  }
}

export async function handleChat(message: string): Promise<string> {
  manageMemory({ role: "user", content: message });

  try {
    const response = await chatWithLLM(message, memory);

    if (typeof response === "string") {
      // TODO: This is a simple way to detect if the LLM couldn't find information.
      // For a more robust solution, consider using a more structured response from the LLM.
      if (response.toLowerCase().includes("not found")) {
        const lastUserMessage = memory.slice().reverse().find((m) => m.role === "user");
        if (lastUserMessage) {
          try {
            const newData = await orchestrateResearch(lastUserMessage.content);
            const researchSummary = "I've updated your results. " + JSON.stringify({
              marketAnalysis: newData.marketAnalysis,
              competitorAnalysis: newData.competitorAnalysis,
              keyInsights: newData.keyInsights,
            });
            manageMemory({ role: "assistant", content: researchSummary });
            return researchSummary;
          } catch (orchestrationError) {
            console.error("Orchestration Error: ", orchestrationError);
            const errorMessage = "I tried to fetch more information, but an error occurred.";
            manageMemory({ role: "assistant", content: errorMessage });
            return errorMessage;
          }
        }
      }
      manageMemory({ role: "assistant", content: response });
      return response;
    }

    const errorMessage = "An error occurred while processing your message.";
    manageMemory({ role: "assistant", content: errorMessage });
    return errorMessage;

  } catch (llmError) {
    console.error("LLM Error in handleChat: ", llmError);
    const errorMessage = "An error occurred while processing your message.";
    manageMemory({ role: "assistant", content: errorMessage });
    return errorMessage;
  }
}
