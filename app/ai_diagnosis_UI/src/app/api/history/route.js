import connectMongo from "@/lib/connectMongo";
import { verifyTokenAndGetUserId } from "@/lib/firebaseAdmin";
import Profile from "@/models/Profile";
import User from "@/models/User";
import { NextResponse } from "next/server";

// Buộc sử dụng dynamic rendering để tránh lỗi static rendering
export const dynamic = 'force-dynamic'; 

export async function GET(req) {
    try {
        // Kết nối MongoDB
        await connectMongo();

        // Xác thực người dùng và lấy userId từ token
        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return NextResponse.json({ message: 'Missing Authorization header' }, { status: 401 });
        }

        // Xác thực token và lấy UID từ Firebase
        const firebaseUid = await verifyTokenAndGetUserId(authHeader);

        // Tìm user trong MongoDB theo UID của Firebase
        const user = await User.findOne({ uid: firebaseUid });
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        // Truy vấn Profile của người dùng đã đăng nhập
        const profiles = await Profile.find({ createdBy: user._id });

        // Trả về dữ liệu dạng JSON
        return NextResponse.json({ profiles });
    } catch (error) {
        console.error('Error fetching profiles:', error);
        return NextResponse.json({ message: 'Failed to fetch profiles', error }, { status: 500 });
    }
}
