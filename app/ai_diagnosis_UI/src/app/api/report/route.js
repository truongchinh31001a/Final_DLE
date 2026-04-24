import { NextResponse } from 'next/server';
import connectMongo from '@/lib/connectMongo';
import Report from '@/models/Report';
import Profile from '@/models/Profile';
import '@/models/User';

export async function POST(req) {
    try {
        // Kết nối MongoDB
        await connectMongo();

        // Parse request body
        const { profileId, comment, imageId } = await req.json();

        // Kiểm tra các trường bắt buộc
        if (!profileId || !comment || !imageId) {
            return NextResponse.json(
                { message: 'Missing required fields' },
                { status: 400 }
            );
        }

        // Tìm Profile theo `profileId`
        const profile = await Profile.findById(profileId);
        if (!profile) {
            return NextResponse.json(
                { message: 'Profile not found' },
                { status: 404 }
            );
        }

        // Tìm thông tin hình ảnh từ `images` trong Profile
        const imageDetails = profile.images.find(image => image._id.toString() === imageId);
        if (!imageDetails) {
            return NextResponse.json(
                { message: 'Image not found in profile' },
                { status: 404 }
            );
        }

        // Lấy `userId` từ `createdBy` trong Profile
        const userId = profile.createdBy;
        if (!userId) {
            return NextResponse.json(
                { message: 'Profile does not have a creator (createdBy)' },
                { status: 400 }
            );
        }

        // Tạo báo cáo mới
        const report = await Report.create({
            profileId,
            comment,
            user: userId, // Lấy từ `createdBy`
            imageDetails, // Lấy từ Profile
        });

        // Cập nhật danh sách báo cáo trong hình ảnh của Profile
        profile.images = profile.images.map(image =>
            image._id.toString() === imageId
                ? {
                    ...image,
                    reports: [...(image.reports || []), report._id],
                }
                : image
        );
        await profile.save();

        return NextResponse.json(
            { message: 'Report created successfully', report },
            { status: 201 }
        );
    } catch (error) {
        console.error('Error creating report:', error);
        return NextResponse.json(
            { message: 'An error occurred while creating the report' },
            { status: 500 }
        );
    }
}

export async function GET(req) {
    try {
        // Kết nối MongoDB
        await connectMongo();

        // Lấy tất cả báo cáo và populate thông tin người dùng
        const reports = await Report.find({})
            .populate('user', 'firstName lastName email')
            .exec();

        // Xử lý và trả về kết quả
        const formattedReports = reports.map((report) => ({
            reportId: report._id,
            profileId: report.profileId,
            comment: report.comment,
            user: {
                name: `${report.user?.firstName || 'Unknown'} ${report.user?.lastName || ''}`.trim(),
                email: report.user?.email || 'No email',
            },
            imageDetails: report.imageDetails,
            createdAt: report.createdAt,
        }));

        return NextResponse.json({ reports: formattedReports }, { status: 200 });
    } catch (error) {
        console.error('Error fetching reports:', error);
        return NextResponse.json(
            { message: 'An error occurred while fetching reports' },
            { status: 500 }
        );
    }
}
