import { randomUUID } from 'crypto';
import path from 'path';
import { promises as fs } from 'fs';

import { NextResponse } from 'next/server';

import connectMongo, { isMongoConfigured } from '@/lib/connectMongo';
import { verifyTokenAndGetUserId } from '@/lib/firebaseAdmin';
import Profile from '@/models/Profile';
import User from '@/models/User';
import { sendImageToThirdPartyAPI } from '@/services/sendImageToThirdPartyAPI';

function buildEphemeralProfile(name, images) {
  return {
    _id: randomUUID(),
    name,
    images,
    isUser: false,
    persisted: false,
    mongoEnabled: false,
    createdAt: new Date().toISOString(),
  };
}

export async function POST(req) {
  const mongoEnabled = isMongoConfigured();
  if (mongoEnabled) {
    await connectMongo();
  }

  const formData = await req.formData();
  const name = formData.get('name');
  const files = formData.getAll('images');
  const modelIdValue = formData.get('modelId');
  const modelId = typeof modelIdValue === 'string' ? modelIdValue : undefined;

  if (!name || files.length === 0) {
    return NextResponse.json({ message: 'Profile name and images are required' }, { status: 400 });
  }

  const authHeader = req.headers.get('Authorization');
  let userId = null;

  if (mongoEnabled) {
    try {
      const firebaseUid = await verifyTokenAndGetUserId(authHeader);
      const user = await User.findOne({ uid: firebaseUid });
      if (!user) {
        return NextResponse.json({ message: 'User not found' }, { status: 404 });
      }
      userId = user._id;
    } catch (error) {
      console.error('Error verifying token or fetching user:', error.message);
    }
  }

  const uploadDir = path.join(process.cwd(), 'public/uploads');
  await fs.mkdir(uploadDir, { recursive: true });

  const images = await Promise.all(
    files.map(async (file) => {
      const filePath = `/uploads/${Date.now()}-${file.name}`;
      const buffer = Buffer.from(await file.arrayBuffer());

      await fs.writeFile(`./public${filePath}`, buffer);

      return {
        _id: randomUUID(),
        filename: file.name,
        path: filePath,
        originalname: file.name,
      };
    }),
  );

  try {
    const updatedImages = await Promise.all(
      images.map(async (image) => {
        try {
          const thirdPartyResult = await sendImageToThirdPartyAPI(`./public${image.path}`, modelId);
          return {
            ...image,
            thirdPartyInfo: thirdPartyResult,
          };
        } catch (error) {
          console.error(`Failed to process image ${image.filename}: ${error.message}`);
          return image;
        }
      }),
    );

    if (!mongoEnabled) {
      const profile = buildEphemeralProfile(name, updatedImages);
      return NextResponse.json({
        message: 'Profile processed successfully without MongoDB persistence',
        profile,
      });
    }

    const profileData = {
      name,
      images,
      isUser: Boolean(userId),
      createdBy: userId || undefined,
    };

    const profile = new Profile(profileData);
    await profile.save();

    profile.images = updatedImages;
    await profile.save();

    const responseProfile = profile.toObject();
    responseProfile.persisted = true;
    responseProfile.mongoEnabled = true;

    return NextResponse.json({
      message: 'Profile created and updated with third-party info successfully',
      profile: responseProfile,
    });
  } catch (error) {
    console.error('Error creating profile:', error.message);
    return NextResponse.json({ message: 'Error creating profile' }, { status: 500 });
  }
}
