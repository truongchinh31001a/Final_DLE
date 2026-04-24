import { NextResponse } from 'next/server';
import { getAdminAuth } from '@/lib/firebaseAdmin';
import connectMongo from '@/lib/connectMongo';
import User from '@/models/User';

export async function DELETE(req) {
  try {
    await connectMongo();

    const { userId } = await req.json();
    const user = await User.findById(userId);

    if (!user) {
      return NextResponse.json({ message: 'User not found' }, { status: 404 });
    }

    await getAdminAuth().deleteUser(user.uid);
    await User.findByIdAndDelete(userId);

    return NextResponse.json({ message: 'User deleted successfully' }, { status: 200 });
  } catch (error) {
    console.error('Error deleting user:', error);
    return NextResponse.json({ message: 'Failed to delete user', error }, { status: 500 });
  }
}
