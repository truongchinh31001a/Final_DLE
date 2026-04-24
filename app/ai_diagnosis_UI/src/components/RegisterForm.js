'use client';

import { Form, Input, Button, Divider, message } from 'antd';
import { useState } from 'react';
import { auth, createUserWithEmailAndPassword } from '@/firebase.config';

const RegisterForm = ({ setActiveTab }) => {
  const [passwordValidations, setPasswordValidations] = useState({
    length: false,
    hasUppercase: false,
    hasNumber: false,
  });
  const [showPasswordRequirements, setShowPasswordRequirements] = useState(false);
  const [loading, setLoading] = useState(false);

  const validatePassword = (password) => {
    setPasswordValidations({
      length: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasNumber: /[0-9]/.test(password),
    });
  };

  const handleRegister = async (values) => {
    setLoading(true);
    const { firstName, lastName, email, password } = values;

    try {
      // Create account in Firebase
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      // Send info to server to create account in MongoDB
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          uid: user.uid,
          email,
          firstName,
          lastName,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Display success message and switch to login form
        message.success('Your account has been created successfully. You can now log in.');
        setActiveTab('login'); // Switch to login form
      } else {
        // Display error message if registration in MongoDB fails
        message.error(data.message || 'Failed to register your account. Please try again.');
      }
    } catch (error) {
      // Display error message if Firebase registration fails
      message.error(error.message || 'There was an error creating your account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center items-center min-h-screen p-5 bg-gray-100">
      <h3 className="text-3xl font-bold mb-5">Register</h3>
      <Form
        name="register"
        onFinish={handleRegister}
        layout="vertical"
        className="w-full max-w-md"
      >
        <Divider className="my-4">Sign up with Email</Divider>

        <Form.Item
          label="Email"
          name="email"
          rules={[{ required: true, message: 'Please input your email!' }]}
        >
          <Input className="h-10" />
        </Form.Item>

        <div className="flex space-x-4">
          <Form.Item
            label="First Name"
            name="firstName"
            className="w-1/2"
            rules={[{ required: true, message: 'Please input your first name!' }]}
          >
            <Input className="h-10" />
          </Form.Item>

          <Form.Item
            label="Last Name"
            name="lastName"
            className="w-1/2"
            rules={[{ required: true, message: 'Please input your last name!' }]}
          >
            <Input className="h-10" />
          </Form.Item>
        </div>

        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Please input your password!' }]}
        >
          <Input.Password
            className="h-10"
            onFocus={() => setShowPasswordRequirements(true)}
            onBlur={() => setShowPasswordRequirements(false)}
            onChange={(e) => validatePassword(e.target.value)}
          />
        </Form.Item>

        <div className={`transition-all duration-500 ${showPasswordRequirements ? 'opacity-100' : 'opacity-0'}`}>
          <p className={`${passwordValidations.length ? 'text-green-500' : 'text-red-500'}`}>
            {passwordValidations.length ? '✓' : '✗'} Minimum 8 characters
          </p>
          <p className={`${passwordValidations.hasUppercase ? 'text-green-500' : 'text-red-500'}`}>
            {passwordValidations.hasUppercase ? '✓' : '✗'} At least one uppercase letter
          </p>
          <p className={`${passwordValidations.hasNumber ? 'text-green-500' : 'text-red-500'}`}>
            {passwordValidations.hasNumber ? '✓' : '✗'} At least one number
          </p>
        </div>

        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('The two passwords do not match!'));
              },
            }),
          ]}
        >
          <Input.Password className="h-10" />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            className="w-full h-12"
            loading={loading}
            disabled={loading || !passwordValidations.length || !passwordValidations.hasUppercase || !passwordValidations.hasNumber}
          >
            {loading ? 'Registering...' : 'Sign Up'}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default RegisterForm;
