import { NextResponse } from 'next/server';
import User from '@/models/User'; // Model User từ MongoDB
import connectMongo from '@/lib/connectMongo';

export async function POST(req) {
  try {
    const { email, firstName, lastName, uid, image } = await req.json();

    // Kiểm tra nếu email hoặc UID không tồn tại
    if (!email || !uid) {
      return NextResponse.json({ message: 'Email and UID are required.' }, { status: 400 });
    }

    // Kết nối với MongoDB
    await connectMongo();

    // Kiểm tra xem người dùng đã tồn tại chưa
    let existingUser = await User.findOne({ email });

    if (existingUser) {
      // Kiểm tra xem tài khoản đã liên kết với Google chưa
      if (!existingUser.isGoogleLogin) {
        // Nếu tài khoản đã tồn tại nhưng chưa liên kết với Google, thực hiện liên kết
        existingUser.isGoogleLogin = true;
        if (!existingUser.uid) {
          existingUser.uid = uid; // Chỉ cập nhật UID nếu nó chưa được gán
        }
        await existingUser.save();
        return NextResponse.json({ message: 'Account linked with Google successfully' }, { status: 200 });
      } else {
        // Nếu tài khoản đã liên kết với Google, chỉ thông báo đăng nhập thành công
        return NextResponse.json({ message: 'Already signed in with Google', user: existingUser }, { status: 200 });
      }
    } else {
      // Nếu tài khoản chưa tồn tại, tạo tài khoản mới
      const newUser = new User({
        uid,
        email,
        firstName: firstName || 'Unknown',
        lastName: lastName || '',
        image,
        isGoogleLogin: true
      });
      await newUser.save();
      return NextResponse.json({ message: 'Google login successful, new account created' }, { status: 201 });
    }
  } catch (error) {
    console.error('Error during Google login:', error);
    return NextResponse.json({ message: error.message || 'Google login failed' }, { status: 500 });
  }
}
