'use client';

import { Form, Input, Button, Divider, message } from 'antd';
import { useRouter } from 'next/navigation';
import GoogleLoginButton from './GoogleLoginButton';
import { useState } from 'react';

const LoginForm = () => {
  const router = useRouter();
  const [loading, setLoading] = useState(false); // Loading state cho cả email và Google

  // Xử lý đăng nhập bằng email/password
  const handleLogin = async (values) => {
    setLoading(true);

    const { email, password } = values;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('Log in success');

        router.push('/');
      } else {
        message.error('Login error')
      }
    } catch (e) {
      message.error('Login error')
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center h-[70vh] bg-gray-100">
      <div className="bg-white p-10 rounded-lg w-full max-w-md">
        <h3 className="text-2xl font-bold mb-5">Login</h3>

        {/* Nút đăng nhập Google */}
        <GoogleLoginButton setLoading={setLoading} />

        <Divider className="my-5">Or login with email</Divider>

        {/* Form đăng nhập bằng email và mật khẩu */}
        <Form name="login" onFinish={handleLogin} layout="vertical">
          <Form.Item
            label="Email"
            name="email"
            rules={[{ required: true, message: 'Please input your email!' }]}
          >
            <Input className="h-10" />
          </Form.Item>

          <Form.Item
            label="Password"
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password className="h-10" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="w-full h-12"
              loading={loading}
            >
              Login
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
};

export default LoginForm;
