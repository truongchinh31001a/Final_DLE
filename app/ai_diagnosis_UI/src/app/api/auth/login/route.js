import { NextResponse } from 'next/server';

export async function POST(req) {
  await req.json().catch(() => null);

  return NextResponse.json(
    { message: 'Login is disabled in this deployment.' },
    { status: 503 }
  );
}
