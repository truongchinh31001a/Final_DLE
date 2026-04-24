'use client';

import { Button, message, Modal, Input } from 'antd';
import { useState } from 'react';
import { auth, googleProvider, signInWithPopup, linkWithCredential, EmailAuthProvider } from '@/firebase.config';
import { getAuth, fetchSignInMethodsForEmail } from 'firebase/auth';
import { useRouter } from 'next/navigation';

const GoogleLoginButton = () => {
  const [loading, setLoading] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [password, setPassword] = useState('');
  const [googleUser, setGoogleUser] = useState(null);
  const router = useRouter();

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      // Sign in with Google
      const googleResult = await signInWithPopup(auth, googleProvider);
      const googleUser = googleResult.user;

      // Get the Auth instance and fetch sign-in methods for the user's email
      const authInstance = getAuth();
      const existingUserMethods = await fetchSignInMethodsForEmail(authInstance, googleUser.email);

      // Kiểm tra nếu phương thức đăng nhập là email/password
      if (existingUserMethods.includes('password')) {
        // Nếu tài khoản email/password đã tồn tại, yêu cầu người dùng nhập mật khẩu
        setGoogleUser(googleUser);
        setPasswordModalVisible(true); // Hiển thị modal để người dùng nhập mật khẩu
      } else {
        // Gửi thông tin người dùng Google lên server để tạo tài khoản MongoDB
        const response = await fetch('/api/auth/google', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: googleUser.email,
            firstName: googleUser.displayName.split(' ')[0],
            lastName: googleUser.displayName.split(' ')[1] || '',
            uid: googleUser.uid,
            image: googleUser.photoURL,
          }),
        });

        const data = await response.json();

        if (response.ok) {
          message.success('Successfully signed in with Google.');
          router.push('/')
        } else {
          message.error(data.message || 'An error occurred while creating your account.');
        }
      }
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkWithPassword = async () => {
    if (!password) {
      message.error('Please enter your password.');
      return;
    }
    try {
      // Tạo credential cho email/password
      const emailCredential = EmailAuthProvider.credential(googleUser.email, password);

      // Liên kết tài khoản Google với tài khoản email/password
      await linkWithCredential(googleUser, emailCredential);

      // Gửi thông tin người dùng Google lên server để tạo tài khoản MongoDB
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: googleUser.email,
          firstName: googleUser.displayName.split(' ')[0],
          lastName: googleUser.displayName.split(' ')[1] || '',
          uid: googleUser.uid,
          image: googleUser.photoURL,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('Google account successfully linked to your existing account.');
      } else {
        message.error(data.message || 'An error occurred while linking your Google account.');
      }

      setPasswordModalVisible(false); // Ẩn modal
    } catch (error) {
      handleError(error);
    }
  };

  const handleError = (error) => {
    if (error.code === 'auth/credential-already-in-use') {
      message.error('This Google account is already linked with another account.');
    } else if (error.code === 'auth/email-already-in-use') {
      message.error('This email is already associated with another account.');
    } else {
      message.error(error.message);
    }
  };

  return (
    <>
      <Button
        type="default"
        block
        className="w-full h-12 flex items-center justify-center"
        loading={loading}
        onClick={handleGoogleSignIn}
      >
        <img src="/google-logo.png" alt="Google logo" className="w-6 h-6 mr-3" />
        Google
      </Button>

      <Modal
        title="Link Google Account"
        visible={passwordModalVisible}
        onOk={handleLinkWithPassword}
        onCancel={() => setPasswordModalVisible(false)}
        okText="Link Account"
        cancelText="Cancel"
      >
        <p>Please enter your password to link your Google account with your existing account.</p>
        <Input.Password
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Modal>
    </>
  );
};

export default GoogleLoginButton;
