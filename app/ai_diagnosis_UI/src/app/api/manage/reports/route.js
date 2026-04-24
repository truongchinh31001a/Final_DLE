import connectMongo, { isMongoConfigured } from '@/lib/connectMongo';
import Report from '@/models/Report';
import '@/models/User';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    if (!isMongoConfigured()) {
      return new Response(JSON.stringify({ reports: [] }), { status: 200 });
    }

    await connectMongo();

    const reports = await Report.find()
      .populate({
        path: 'user',
        select: 'firstName lastName email',
      })
      .exec();

    const formattedReports = reports.map((report) => ({
      reportId: report._id,
      profileId: report.profileId,
      comment: report.comment,
      user: report.user
        ? {
            name: `${report.user.firstName} ${report.user.lastName}`,
            email: report.user.email,
          }
        : {
            name: 'Unknown',
            email: 'No email',
          },
      imageDetails: report.imageDetails,
      createdAt: report.createdAt,
    }));

    return new Response(JSON.stringify({ reports: formattedReports }), {
      status: 200,
    });
  } catch (error) {
    console.error('Error fetching reports:', error);
    return new Response(
      JSON.stringify({ message: 'Failed to fetch reports', error }),
      { status: 500 }
    );
  }
}
