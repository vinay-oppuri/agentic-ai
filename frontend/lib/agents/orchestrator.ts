
import { competitorScout } from "./competitor-scout";
import { trendScraper } from "./trend-scraper";
import { techMiner } from "./techMiner";
import { summarizer } from "./summarizer";
import { NextResponse } from "next/server";
import { db } from "@/db";
import { researchReport } from "@/db/schema";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

type AgentResult<T> = T | NextResponse<{ error: string }>;

const isError = <T>(res: AgentResult<T>): res is NextResponse<{ error: string }> => res instanceof NextResponse;

export async function orchestrateResearch(idea: string) {
  const session = await auth.api.getSession({ headers: await headers() });

  if (!session?.user?.id) {
    throw new Error("User must be logged in to generate a research report.");
  }

  const [competitorsResult, techResult, trendsResult] = await Promise.allSettled([
    competitorScout(idea),
    techMiner(idea),
    trendScraper(idea),
  ]);

  const competitors = competitorsResult.status === 'fulfilled' && !isError(competitorsResult.value) ? competitorsResult.value.competitors || [] : [];
  const tech = techResult.status === 'fulfilled' && !isError(techResult.value) ? techResult.value.papers || [] : [];
  const trends = trendsResult.status === 'fulfilled' && !isError(trendsResult.value) ? trendsResult.value.trends || [] : [];

  const summary = await summarizer({ idea, competitors, tech, trends });

  const report = {
    idea,
    marketAnalysis: summary.marketAnalysis || "No market analysis available.",
    competitorAnalysis: summary.competitorAnalysis || "No competitor analysis available.",
    keyInsights: summary.keyInsights || "No key insights available.",
    generatedAt: new Date(),
    userId: session.user.id
  }

  await db.insert(researchReport).values(report);

  return report;
}
