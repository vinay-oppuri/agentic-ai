export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";
import { orchestrateResearch } from "@/lib/agents/orchestrator";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const idea = body?.idea;

    if (!idea || typeof idea !== "string") {
      return NextResponse.json(
        { error: "Missing or invalid 'idea' in request body." },
        { status: 400 }
      );
    }

    console.log("Calling Orchestrator....");
    const result = await orchestrateResearch(idea);
    console.log("Orchestrator is done.");

    return NextResponse.json(result);
  } catch (err) {
    console.error("API Error:", err);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
