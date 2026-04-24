import mongoose from 'mongoose';

const reportSchema = new mongoose.Schema({
  profileId: { type: mongoose.Schema.Types.ObjectId, ref: 'Profile', required: true }, 
  comment: { type: String, required: true }, 
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true }, 
  createdAt: { type: Date, default: Date.now }, 
  imageDetails: { 
    filename: { type: String, required: true },
    path: { type: String, required: true },
    originalname: { type: String, required: true },
    thirdPartyInfo: { 
      predictions: [[String]], 
    },
    status: { type: Boolean, default: true }, 
  },
});

const Report = mongoose.models.Report || mongoose.model('Report', reportSchema);

export default Report;
