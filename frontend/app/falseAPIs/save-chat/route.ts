import { db } from "@/db";
import { chats } from "@/db/schema";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { user_id, role, message } = await req.json();

    if (!user_id || !role || !message)
      return NextResponse.json({ error: "Missing fields" }, { status: 400 });

    await db.insert(chats).values({
      user_id,
      role,
      message,
    });

    return NextResponse.json({ success: true });
  } catch (e) {
    console.error("Error saving chat:", e);
    return NextResponse.json({ error: "Failed to save chat" }, { status: 500 });
  }
}