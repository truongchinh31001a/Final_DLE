'use client';

import { Avatar, Dropdown, Menu, Select } from 'antd';
import {
  BarChartOutlined,
  FileSearchOutlined,
  HomeOutlined,
  InfoCircleOutlined,
  UserOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth, firebaseAuthEnabled, onAuthStateChanged, signOut } from '@/firebase.config';
import {
  AI_MODEL_OPTIONS,
  AI_MODEL_STORAGE_KEY,
  DEFAULT_AI_MODEL_ID,
  isValidAIModelId,
} from '@/lib/aiModels';

export default function Header() {
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState(DEFAULT_AI_MODEL_ID);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedModelId = window.localStorage.getItem(AI_MODEL_STORAGE_KEY);
      if (isValidAIModelId(storedModelId)) {
        setSelectedModelId(storedModelId);
      }
    }

    if (!firebaseAuthEnabled || !auth) {
      setUser(null);
      setIsAdmin(false);
      return undefined;
    }

    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (!currentUser) {
        setUser(null);
        setIsAdmin(false);
        return;
      }

      try {
        const response = await fetch('/api/getUserDetails', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ uid: currentUser.uid }),
        });

        if (!response.ok) {
          console.error('Failed to fetch user data:', response.status);
          return;
        }

        const data = await response.json();
        setUser(data);
        setIsAdmin(Boolean(data?.isAdmin));
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleLogout = () => {
    if (!auth) {
      return;
    }

    signOut(auth)
      .then(() => {
        setUser(null);
        setIsAdmin(false);
        router.push('/');
      })
      .catch((error) => {
        console.error('Error signing out:', error);
      });
  };

  const handleModelChange = (value) => {
    setSelectedModelId(value);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(AI_MODEL_STORAGE_KEY, value);
    }
  };

  const menu = (
    <Menu>
      <Menu.Item key="profile">
        <Link href="/profile">Profile</Link>
      </Menu.Item>
      <Menu.Item key="history">
        <Link href="/history">History</Link>
      </Menu.Item>
      {isAdmin && (
        <Menu.Item key="manage">
          <Link href="/manage">Manage</Link>
        </Menu.Item>
      )}
      <Menu.Item key="logout" onClick={handleLogout}>
        Logout
      </Menu.Item>
    </Menu>
  );

  const items = [
    { key: 'home', icon: <HomeOutlined /> },
    { key: 'diagnosis', icon: <FileSearchOutlined /> },
    { key: 'metrics', icon: <BarChartOutlined /> },
    { key: 'about', icon: <InfoCircleOutlined /> },
  ];

  return (
    <header className="fixed left-0 top-0 z-50 flex w-full items-center justify-between border-b border-gray-300 bg-white p-4">
      <div className="flex items-center">
        <Link href="/">
          <img src="/LOGO.png" alt="Logo" className="h-20" />
        </Link>
      </div>

      <nav className="ml-6 flex flex-grow justify-start space-x-6">
        {items.map((item) => (
          <Link
            href={item.key === 'home' ? '/' : `/${item.key}`}
            key={item.key}
            className="flex items-center text-blue-500 transition-colors hover:text-blue-700"
          >
            <span className="mr-2">{item.icon}</span>
            {item.key.charAt(0).toUpperCase() + item.key.slice(1)}
          </Link>
        ))}
      </nav>

      <div className="flex items-center space-x-4">
        {!firebaseAuthEnabled && (
          <div className="flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-2">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-500">
              Model
            </span>
            <Select
              value={selectedModelId}
              onChange={handleModelChange}
              options={AI_MODEL_OPTIONS}
              bordered={false}
              popupMatchSelectWidth={false}
              className="min-w-[180px]"
            />
          </div>
        )}
        {user ? (
          <Dropdown overlay={menu} trigger={['click']}>
            <div className="flex cursor-pointer items-center">
              <Avatar icon={<UserOutlined />} src={user?.image || '/default-avatar.png'} />
              <span className="ml-2 text-gray-700">{`${user.firstName} ${user.lastName}`}</span>
            </div>
          </Dropdown>
        ) : !firebaseAuthEnabled ? null : (
          <Link href="/auth">
            <button className="rounded bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700">
              Login
            </button>
          </Link>
        )}
      </div>
    </header>
  );
}
