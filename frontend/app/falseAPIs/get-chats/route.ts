import { NextResponse } from "next/server";
import { db } from "@/db";
import { chats } from "@/db/schema";
import { desc, eq } from "drizzle-orm";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const user_id = searchParams.get("user_id");

  if (!user_id)
    return NextResponse.json({ error: "Missing user_id" }, { status: 400 });

  const history = await db
    .select()
    .from(chats)
    .where(eq(chats.user_id, user_id))
    .orderBy(desc(chats.created_at));

  return NextResponse.json(history);
}