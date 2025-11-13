import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: { user_id: string } }
) {
  const { user_id } = params;
  const res = await fetch(`http://localhost:8000/api/get-chats/${user_id}`);
  const data = await res.json();
  return NextResponse.json(data);
}