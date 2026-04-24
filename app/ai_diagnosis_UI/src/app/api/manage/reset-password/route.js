import { NextResponse } from 'next/server';
import { getAdminAuth } from '@/lib/firebaseAdmin';
import connectMongo from '@/lib/connectMongo';
import User from '@/models/User';

export async function POST(req) {
  try {
    await connectMongo();

    const { userId, newPassword } = await req.json();
    const user = await User.findById(userId);

    if (!user) {
      return NextResponse.json({ message: 'User not found' }, { status: 404 });
    }

    await getAdminAuth().updateUser(user.uid, {
      password: newPassword,
    });

    return NextResponse.json({ message: 'Password updated successfully' }, { status: 200 });
  } catch (error) {
    console.error('Error updating password:', error);
    return NextResponse.json({ message: 'Failed to update password', error }, { status: 500 });
  }
}
