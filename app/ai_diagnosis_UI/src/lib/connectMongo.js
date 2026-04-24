import mongoose from 'mongoose';

export function isMongoConfigured() {
  return Boolean(process.env.MONGO_URI && process.env.MONGO_URI.trim());
}

const connectMongo = async () => {
  if (!isMongoConfigured()) {
    throw new Error('MongoDB is disabled because MONGO_URI is not set');
  }

  if (mongoose.connection.readyState >= 1) {
    return;
  }

  try {
    await mongoose.connect(process.env.MONGO_URI, {
      dbName: 'deepmed',
      serverSelectionTimeoutMS: 30000,
    });
    console.log('Connected to MongoDB successfully');
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    throw new Error('MongoDB connection failed');
  }
};

export default connectMongo;
