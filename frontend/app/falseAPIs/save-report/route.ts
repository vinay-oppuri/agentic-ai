import { db } from "@/db";
import { reports } from "@/db/schema";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { idea, resultJson, reportMd } = await req.json();

    if (!idea || !resultJson || !reportMd)
      return NextResponse.json({ error: "Missing fields" }, { status: 400 });

    await db.insert(reports).values({
      idea,
      result_json: resultJson,
      report_md: reportMd,
    });

    return NextResponse.json({ success: true });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: "Failed to save report" }, { status: 500 });
  }
}