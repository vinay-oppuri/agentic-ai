import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { HumanMessage } from "@langchain/core/messages";
import { NextResponse } from "next/server";


export async function GET() {

  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-pro",
    temperature: 0,
    apiKey: process.env.GEMINI_API_KEY,
  });

  try {
    const messages = [
      new HumanMessage("Hello, tell me a quick fact about space."),
    ];

    console.log("Invoking model.....")

    const res = await llm.invoke(messages)
    console.log(res.content)

    // return NextResponse.json({ reply: response.content });
    return NextResponse.json(res)

  } catch (error) {
    console.error("LLM Error: ", error);

    return NextResponse.json(
      { error: "Internal Server Error", message: (error as Error).message },
      { status: 500 }
    );
  }
}