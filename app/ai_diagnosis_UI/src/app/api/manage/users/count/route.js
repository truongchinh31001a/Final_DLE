import { NextResponse } from 'next/server';
import connectMongo, { isMongoConfigured } from '@/lib/connectMongo';
import User from '@/models/User';

export const dynamic = 'force-dynamic';

export async function GET() {
  if (!isMongoConfigured()) {
    return NextResponse.json({ count: 0, data: [] });
  }

  await connectMongo();
  const userCount = await User.countDocuments();
  return NextResponse.json({ count: userCount, data: [] });
}
