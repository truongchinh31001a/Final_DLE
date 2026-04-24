'use client';

import { Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';

export default function ImagePreview({ fileList, handlePreview, handleRemove }) {
  return (
    <div className="mb-4 text-center">
      <p className="text-blue-400 font-medium mb-2">selectedFiles</p>
      <div className="flex justify-center flex-wrap gap-2 sm:gap-4">
        {fileList.map((file) => (
          <div
            key={file.uid}
            className="relative w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24"
          >
            <img
              src={URL.createObjectURL(file.originFileObj)}
              alt={file.name}
              className="w-full h-full object-cover rounded-md shadow-lg cursor-pointer"
              onClick={() => handlePreview(file)}
            />
            <Button
              type="text"
              icon={<CloseOutlined />}
              className="absolute top-0 right-0 text-red-500 bg-white rounded-full shadow-lg"
              style={{ padding: '2px', fontSize: '12px' }}
              onClick={() => handleRemove(file)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
