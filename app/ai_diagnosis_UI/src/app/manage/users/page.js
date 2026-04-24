'use client';

import { useEffect, useState } from 'react';
import { Avatar, Button, Modal, Spin, Table, message } from 'antd';
import { IdcardOutlined } from '@ant-design/icons';
import { auth } from '@/firebase.config';

export default function ManageUsers() {
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [users, setUsers] = useState([]);
  const [currentUserUID, setCurrentUserUID] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const getCurrentUserUID = async () => {
    const user = auth?.currentUser;
    if (user) {
      setCurrentUserUID(user.uid);
    } else {
      setLoadingUsers(false);
    }
  };

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await fetch('/api/manage/users');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message);
      }

      const filteredUsers = data.users.filter((user) => user.uid !== currentUserUID);
      setUsers(filteredUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleResetPassword = async (userId) => {
    const newPassword = prompt('Enter new password for the user:');

    if (!newPassword) {
      return;
    }

    try {
      const response = await fetch('/api/manage/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, newPassword }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('Password updated successfully');
      } else {
        message.error(`Error: ${data.message}`);
      }
    } catch (error) {
      console.error('Error updating password:', error);
      message.error('Failed to update password');
    }
  };

  const handleDeleteUser = async (userId) => {
    try {
      const response = await fetch('/api/manage/delete-user', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId }),
      });

      const data = await response.json();

      if (response.ok) {
        message.success('User deleted successfully');
        fetchUsers();
      } else {
        message.error(`Error: ${data.message}`);
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      message.error('Failed to delete user');
    }
  };

  useEffect(() => {
    getCurrentUserUID();
  }, []);

  useEffect(() => {
    if (currentUserUID) {
      fetchUsers();
    }
  }, [currentUserUID]);

  const showUserDetails = (user) => {
    setSelectedUser(user);
    setIsModalVisible(true);
  };

  const handleCloseModal = () => {
    setIsModalVisible(false);
    setSelectedUser(null);
  };

  const userColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (_, record) => `${record.firstName} ${record.lastName}`,
    },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button type="primary" onClick={() => showUserDetails(record)} icon={<IdcardOutlined />} />
      ),
    },
  ];

  return (
    <div className="mx-auto mt-10 max-w-6xl p-6">
      {!auth && (
        <div className="mb-6 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 text-yellow-800">
          User management is unavailable because authentication is disabled.
        </div>
      )}

      <h2 className="mb-6 text-center text-2xl font-semibold">Manage Users</h2>
      {loadingUsers ? (
        <div className="flex h-64 items-center justify-center">
          <Spin size="large" />
        </div>
      ) : (
        <Table
          dataSource={users}
          columns={userColumns}
          rowKey="_id"
          pagination={{
            defaultPageSize: 5,
            showSizeChanger: true,
            pageSizeOptions: ['5', '10', '20', '50'],
          }}
          className="w-full rounded-lg"
          style={{ fontSize: '16px' }}
        />
      )}

      <Modal
        title={<h2 className="text-lg font-bold">User Details</h2>}
        visible={isModalVisible}
        onCancel={handleCloseModal}
        footer={null}
        className="overflow-hidden rounded-lg"
      >
        {selectedUser && (
          <div className="flex flex-col items-center space-y-4">
            <Avatar
              size={100}
              src={selectedUser.image || '/default-avatar.png'}
              className="mb-4"
            />
            <div className="w-full space-y-2 text-left">
              <p><strong>First Name:</strong> {selectedUser.firstName}</p>
              <p><strong>Last Name:</strong> {selectedUser.lastName}</p>
              <p><strong>Email:</strong> {selectedUser.email}</p>
              <p><strong>Google Login:</strong> {selectedUser.isGoogleLogin ? 'Yes' : 'No'}</p>
              <p><strong>Admin:</strong> {selectedUser.isAdmin ? 'Yes' : 'No'}</p>
            </div>

            <div className="mt-6 flex justify-center space-x-4">
              <Button
                className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50"
                onClick={() => handleResetPassword(selectedUser._id)}
              >
                Reset Password
              </Button>
              <Button
                className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-opacity-50"
                onClick={() => handleDeleteUser(selectedUser._id)}
              >
                Delete
              </Button>
            </div>

            <div className="mt-4 flex w-full justify-end">
              <Button
                key="close"
                onClick={handleCloseModal}
                className="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-600 focus:ring-opacity-50"
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
