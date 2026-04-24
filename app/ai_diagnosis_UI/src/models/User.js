import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  uid: { type: String, required: true, unique: true },  // Firebase User ID
  email: { type: String, required: true, unique: true }, // Email của người dùng
  firstName: { type: String, required: true },
  lastName: { type: String, required: true },
  image: { type: String },
  isGoogleLogin: { type: Boolean, default: false },  // Xác định đăng ký bằng Google Sign-in
  isAdmin: { type: Boolean, default: false }  // Thêm thuộc tính isAdmin để xác định quyền quản trị viên
}, { timestamps: true });

const User = mongoose.models.User || mongoose.model('User', userSchema);

export default User;
