import { NextResponse } from 'next/server';
import Profile from '@/models/Profile';
import connectMongo from '@/lib/connectMongo';

export async function GET(req, { params }) {
  const { id } = params; // Lấy ID từ URL

  try {
    await connectMongo(); // Kết nối đến MongoDB

    const profile = await Profile.findById(id); // Tìm hồ sơ theo ID

    if (!profile) {
      return NextResponse.json({ message: 'Profile not found' }, { status: 404 });
    }

    return NextResponse.json({ profile }, { status: 200 });
  } catch (error) {
    console.error('Error fetching profile:', error);
    return NextResponse.json({ message: 'Error fetching profile' }, { status: 500 });
  }
}
