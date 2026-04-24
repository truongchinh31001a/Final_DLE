'use client';

import { Layout, Menu } from 'antd';
import { UserOutlined, FileOutlined, HomeOutlined, SettingOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

const { Sider, Content } = Layout;

export default function ManageLayout({ children }) {
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh', marginTop: '20px' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={() => setCollapsed(!collapsed)}
        className="fixed left-0 h-screen bg-gray-800"
      >
        <div className="logo h-16 my-4 mx-2 text-center text-white text-xl">
          
        </div>
        <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline">
          <Menu.Item key="1" icon={<HomeOutlined />} onClick={() => router.push('/manage')}>
            Dashboard
          </Menu.Item>
          <Menu.Item key="2" icon={<UserOutlined />} onClick={() => router.push('/manage/users')}>
            Manage Users
          </Menu.Item>
          <Menu.Item key="3" icon={<FileOutlined />} onClick={() => router.push('/manage/reports')}>
            Manage Reports
          </Menu.Item>
        </Menu>
      </Sider>

      <Layout className={`transition-all duration-300 ${collapsed ? 'ml-20' : 'ml-60'}`}>
        <Content className="p-6">{children}</Content>
      </Layout>
    </Layout>
  );
}
