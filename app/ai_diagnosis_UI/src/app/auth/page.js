'use client';

import { Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';

export default function AuthPage() {
  const router = useRouter();

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <div className="absolute left-4 top-4 z-50">
        <Button type="link" onClick={() => router.back()} icon={<ArrowLeftOutlined />}>
          Back
        </Button>
      </div>

      <div className="w-full max-w-xl rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900">Authentication Disabled</h1>
        <p className="mt-4 text-base text-gray-600">
          This deployment is running without Firebase authentication, so login, registration, and password reset are currently unavailable.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Button onClick={() => router.push('/')}>Go Home</Button>
          <Button type="primary" onClick={() => router.back()}>
            Back
          </Button>
        </div>
      </div>
    </div>
  );
}
