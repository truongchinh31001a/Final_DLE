import { NextResponse } from 'next/server';

export async function POST(req) {
  await req.json().catch(() => null);

  return NextResponse.json(
    { message: 'Password reset is disabled because authentication is turned off.' },
    { status: 503 }
  );
}
