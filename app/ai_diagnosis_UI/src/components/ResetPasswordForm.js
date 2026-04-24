'use client';

import { Form, Input, Button, message } from 'antd';
import { useState } from 'react';

const ResetPasswordForm = ({ setLoading, setCurrentForm }) => { // Thêm setCurrentForm để chuyển đổi form
  const [formLoading, setFormLoading] = useState(false); // State for form loading

  const handleResetPassword = async (values) => {
    setFormLoading(true); // Set loading state to true when sending request
    if (setLoading) setLoading(true); // Optional external loading handler

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: values.email }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('Password reset link has been sent to your email.');
        setTimeout(() => {
          // Chuyển về lại form đăng nhập
          setCurrentForm('login'); // Chuyển về form login trong cùng trang
        }, 500); // Delay for 2 seconds
      } else {
        message.error(data.message || 'An error occurred while resetting password.');
      }
    } catch (error) {
      message.error('An error occurred. Please try again.');
    } finally {
      setFormLoading(false); // Set loading state back to false
      if (setLoading) setLoading(false); // Optional external loading handler
    }
  };

  return (
    <div className="flex flex-col justify-center items-center h-screen bg-gray-100">
      <h3 className="text-3xl font-bold mb-5">Reset Password</h3>
      <Form
        name="reset-password"
        onFinish={handleResetPassword}
        layout="vertical"
        className="w-full max-w-md"
      >
        <Form.Item
          label="Email"
          name="email"
          rules={[{ required: true, message: 'Please enter your email address' }]}
        >
          <Input className="h-10" />
        </Form.Item>
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            className="w-full h-12"
            loading={formLoading} // Use the correct loading state
            disabled={formLoading} // Disable button while loading
          >
            Send Reset Link
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default ResetPasswordForm;
