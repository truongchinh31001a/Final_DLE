import { NextResponse } from 'next/server';
import connectMongo, { isMongoConfigured } from '@/lib/connectMongo';
import User from '@/models/User';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    if (!isMongoConfigured()) {
      return NextResponse.json({ users: [] });
    }

    await connectMongo();
    const users = await User.find();

    return NextResponse.json({ users });
  } catch (error) {
    console.error('Error fetching users:', error);
    return NextResponse.json({ message: 'Failed to fetch users' }, { status: 500 });
  }
}
