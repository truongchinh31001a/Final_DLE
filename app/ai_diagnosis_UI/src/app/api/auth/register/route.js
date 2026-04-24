import { NextResponse } from 'next/server';
import User from '@/models/User';
import connectMongo from '@/lib/connectMongo';

export async function POST(req) {
  try {
    await connectMongo();

    const { uid, email, firstName, lastName } = await req.json();

    if (!uid || !email || !firstName || !lastName) {
      return NextResponse.json({ message: "All fields are required" }, { status: 400 });
    }

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return NextResponse.json({ message: "User already exists" }, { status: 400 });
    }

    const newUser = new User({ uid, email, firstName, lastName });
    await newUser.save();

    return NextResponse.json({ message: "User registered successfully", user: newUser }, { status: 201 });

  } catch (e) {
    console.error('Error in registration:', e);
    return NextResponse.json({ message: e.message || 'Internal Server Error' }, { status: 500 });
  }
}