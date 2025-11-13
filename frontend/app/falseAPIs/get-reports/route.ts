// app/api/get-reports/route.ts
import { NextResponse } from "next/server";
import { db } from "@/db";           // ✅ adjust path to your Drizzle instance
import { reports } from "@/db/schema";  // ✅ table name you defined earlier
import { desc } from "drizzle-orm";

export async function GET() {
  try {
    const data = await db
      .select()
      .from(reports)
      .orderBy(desc(reports.created_at));

    return NextResponse.json(data);
  } catch (error) {
    console.error("❌ Error fetching reports:", error);
    return NextResponse.json(
      { error: "Failed to fetch reports" },
      { status: 500 }
    );
  }
}