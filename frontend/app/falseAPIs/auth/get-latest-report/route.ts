import { NextResponse } from "next/server";
import { db } from "@/db";
import { reports } from "@/db/schema";
import { desc } from "drizzle-orm";

export async function GET() {
  try {
    const [latest] = await db
      .select()
      .from(reports)
      .orderBy(desc(reports.created_at))
      .limit(1);

    if (!latest) {
      return NextResponse.json({ error: "No report found" }, { status: 404 });
    }

    return NextResponse.json(latest);
  } catch (err) {
    console.error("Error fetching latest report:", err);
    return NextResponse.json({ error: "Failed to fetch latest report" }, { status: 500 });
  }
}
