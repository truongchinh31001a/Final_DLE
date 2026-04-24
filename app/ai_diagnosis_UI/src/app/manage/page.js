'use client';

import { useState, useEffect } from 'react';
import { Card, Col, Row, Statistic, Spin, message } from 'antd';
import { UserOutlined, FileTextOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ManageDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [userCount, setUserCount] = useState(0);
  const [reportCount, setReportCount] = useState(0);
  const [userData, setUserData] = useState([]);

  // Fetch statistics
  const fetchStatistics = async () => {
    setLoading(true);
    try {
      // Fetch user count
      const userResponse = await fetch('/api/manage/users/count');
      const { count: userCountData, data: userChartData } = await userResponse.json();
      setUserCount(userCountData);
      setUserData(userChartData); // Assuming API provides time-based user count data

      // Fetch report count
      const reportResponse = await fetch('/api/manage/reports/count');
      const { count: reportCountData } = await reportResponse.json();
      setReportCount(reportCountData);
    } catch (error) {
      console.error('Error fetching statistics:', error);
      message.error('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  return (
    <div className="mt-10 mx-auto max-w-6xl p-6">
      <h1 className="text-2xl font-bold mb-6 text-center">Admin Dashboard</h1>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={16}>
            <Col span={12}>
              <Card className="shadow-lg rounded-lg" bordered={false}>
                <Statistic
                  title="Total Users"
                  value={userCount}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card className="shadow-lg rounded-lg" bordered={false}>
                <Statistic
                  title="Total Reports"
                  value={reportCount}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Biểu đồ người dùng */}
          <h2 className="text-xl font-bold mt-8 mb-4 text-center">User Growth Over Time</h2>
          <div className="bg-white rounded-lg p-4">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={userData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#8884d8" activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
