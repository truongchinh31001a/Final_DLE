'use client';

import { useState, useEffect } from 'react';
import { Table, Button, Spin, message, Input, Avatar, DatePicker, Modal } from 'antd';
import { SearchOutlined, FileImageOutlined, DownloadOutlined } from '@ant-design/icons';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import dayjs from 'dayjs';

export default function ManageReports() {
  const [loadingReports, setLoadingReports] = useState(true);
  const [reports, setReports] = useState([]);
  const [filteredReports, setFilteredReports] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [dateRange, setDateRange] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  // Fetch Reports
  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const response = await fetch('/api/manage/reports');
      const data = await response.json();
      setReports(data.reports);
      setFilteredReports(data.reports);
    } catch (error) {
      console.error('Error fetching reports:', error);
      message.error('Failed to load reports');
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Search Reports
  const handleReportSearch = (e) => {
    const value = e.target.value.toLowerCase();
    const filtered = reports.filter((report) =>
      report.comment.toLowerCase().includes(value)
    );
    setFilteredReports(filtered);
  };

  // Filter by Date
  const handleDateRangeChange = (dates) => {
    setDateRange(dates);
    if (dates && dates.length === 2) {
      const [startDate, endDate] = dates;
      const filtered = reports.filter((report) => {
        const reportDate = dayjs(report.createdAt);
        return reportDate.isAfter(startDate) && reportDate.isBefore(endDate);
      });
      setFilteredReports(filtered);
    } else {
      setFilteredReports(reports);
    }
  };

  // Download Images as ZIP
  const handleDownloadZip = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select at least one report.');
      return;
    }

    const zip = new JSZip();

    for (const reportId of selectedRowKeys) {
      const report = reports.find((report) => report._id === reportId);
      if (report && report.imageDetails) {
        const imageUrl = report.imageDetails.path;
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        zip.file(report.imageDetails.filename, blob);
      }
    }

    zip.generateAsync({ type: 'blob' }).then((content) => {
      saveAs(content, `selected_reports.zip`);
    });
  };

  // Open Modal for Image
  const handleImageClick = (image) => {
    setSelectedImage(image);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedImage(null);
  };

  // Table Columns
  const reportColumns = [
    {
      title: 'Image',
      dataIndex: ['imageDetails', 'path'],
      key: 'image',
      render: (path, record) => (
        <Avatar
          src={path}
          size={64}
          icon={<FileImageOutlined />}
          onClick={() => handleImageClick(record.imageDetails)}
          style={{ cursor: 'pointer' }}
        />
      ),
    },
    {
      title: 'Comment',
      dataIndex: 'comment',
      key: 'comment',
      render: (comment) => <span className="text-gray-700">{comment}</span>,
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      render: (user) =>
        user ? (
          <span className="text-gray-700">{`${user.name}`}</span>
        ) : (
          <span className="text-gray-500">Unknown</span>
        ),
    },
    {
      title: 'Diagnosis',
      dataIndex: ['imageDetails', 'thirdPartyInfo', 'predictions'],
      key: 'thirdPartyInfo',
      render: (predictions) =>
        predictions ? (
          predictions.map((prediction, index) => (
            <span key={index} className="text-sm text-gray-700">
              {prediction.join(', ')}
            </span>
          ))
        ) : (
          'No Data'
        ),
    },
    {
      title: 'Created At',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (createdAt) => dayjs(createdAt).format('DD/MM/YYYY HH:mm'),
    },
  ];

  return (
    <div className="mt-10 mx-auto max-w-6xl p-6">
      <h2 className="text-2xl font-semibold mb-6 text-center">Manage Reports</h2>

      <div className="flex justify-between items-center mb-6">
        <Input
          placeholder="Search reports by comment"
          prefix={<SearchOutlined />}
          allowClear
          onChange={handleReportSearch}
          className="w-1/3"
        />
        <DatePicker.RangePicker onChange={handleDateRangeChange} />
      </div>

      {loadingReports ? (
        <div className="flex justify-center items-center h-64">
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Table
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
            }}
            dataSource={filteredReports}
            columns={reportColumns}
            rowKey="_id"
            pagination={{ pageSize: 5 }}
          />

          {selectedRowKeys.length > 0 && (
            <div className="flex justify-end mt-4">
              <Button
                icon={<DownloadOutlined />}
                className="bg-blue-500 text-white"
                onClick={handleDownloadZip}
              >
                Download
              </Button>
            </div>
          )}
        </>
      )}

      <Modal open={isModalOpen} footer={null} onCancel={handleModalClose}>
        {selectedImage && (
          <div>
            <img
              src={selectedImage.path}
              alt={selectedImage.filename}
              style={{ width: '100%', borderRadius: '8px' }}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}
