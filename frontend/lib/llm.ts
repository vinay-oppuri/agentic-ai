import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { HumanMessage, AIMessage } from "@langchain/core/messages";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export async function chatWithLLM(prompt: string, history: Message[]) {

  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-pro",
    temperature: 0,
    apiKey: process.env.GEMINI_API_KEY,
  });

  try {
    const messages = history.map((m) =>
      m.role == "user"
        ? new HumanMessage(m.content)
        : new AIMessage(m.content)
    )

    messages.push(new HumanMessage(prompt))

    const response = await llm.invoke(messages)

    return response.content?.toString() || ""
  } catch (error) {
    console.error("LLM Error: ", error)
    return ""
  }
}