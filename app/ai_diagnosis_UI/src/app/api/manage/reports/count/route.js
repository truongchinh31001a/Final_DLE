import { NextResponse } from 'next/server';
import connectMongo, { isMongoConfigured } from '@/lib/connectMongo';
import Report from '@/models/Report';

export const dynamic = 'force-dynamic';

export async function GET() {
  if (!isMongoConfigured()) {
    return NextResponse.json({ count: 0 });
  }

  await connectMongo();
  const reportCount = await Report.countDocuments();
  return NextResponse.json({ count: reportCount });
}
