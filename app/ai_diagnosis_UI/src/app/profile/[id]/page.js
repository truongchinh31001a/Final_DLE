'use client';

import { useState, useEffect } from 'react';
import { Spin, Modal, Button } from 'antd';
import { useParams } from 'next/navigation';

export default function ProfileDetail() {
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('ear');

  // Function to call API to fetch profile data based on ID
  const fetchProfileData = async () => {
    try {
      const response = await fetch(`/api/profiles/${id}`);
      const data = await response.json();
      setProfile(data.profile);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch profile data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchProfileData();
    }
  }, [id]);

  const handleImageClick = (image) => {
    setSelectedImage(image);
    setModalOpen(true);
  };

  const categorizeImages = (images, category) => {
    return images
      .filter(image => image.status) // Only show images where status is true
      .filter(image =>
        image.thirdPartyInfo?.predictions?.some(prediction =>
          prediction[0].toLowerCase().includes(category.toLowerCase())
        )
      );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spin size="large" />
      </div>
    );
  }

  if (!profile) {
    return <p className="text-center text-lg mt-20">No profile found.</p>;
  }

  const earImages = categorizeImages(profile.images, 'ear');
  const noseImages = categorizeImages(profile.images, 'nose');
  const throatImages = categorizeImages(profile.images, 'throat');

  const currentImages = selectedCategory === 'ear' ? earImages : selectedCategory === 'nose' ? noseImages : throatImages;

  return (
    <div className="min-h-screen bg-gray-50 flex mt-20">
      <div className="w-1/4 bg-white p-6 border-r mt-10">
        <h3 className="text-xl font-semibold mb-6">disease area</h3>
        <div className="flex flex-col space-y-4">
          <Button className="w-full" onClick={() => setSelectedCategory('ear')} type={selectedCategory === 'ear' ? 'primary' : 'default'}>Ear </Button>
          <Button className="w-full" onClick={() => setSelectedCategory('nose')} type={selectedCategory === 'nose' ? 'primary' : 'default'}>Nose </Button>
          <Button className="w-full" onClick={() => setSelectedCategory('throat')} type={selectedCategory === 'throat' ? 'primary' : 'default'}>Throat </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-grow p-8 mt-10">

        {/* Image Gallery */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {currentImages.length > 0 ? currentImages.map((image, index) => (
            <div
              key={index}
              className="relative cursor-pointer rounded-lg overflow-hidden shadow-lg transition-transform transform hover:scale-105"
              onClick={() => handleImageClick(image)}
            >
              <img
                src={image.path}
                alt={image.originalname}
                className="w-full h-48 object-cover"
              />
              <div className="p-4 bg-white">
                {image.thirdPartyInfo?.predictions?.[0]?.[1] && (
                  <p className="text-gray-600">
                    <strong>Diagnosis:</strong> {image.thirdPartyInfo.predictions[0][1]}
                  </p>
                )}
              </div>
            </div>
          )) : (
            <p>No images found in this category.</p>
          )}
        </div>
      </div>

      <Modal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={800}
      >
        {selectedImage && (
          <div>
            <img
              src={selectedImage.path}
              alt={selectedImage.originalname}
              style={{ width: '100%', height: 'auto' }}
            />
            <h3 className="mt-4 text-lg font-semibold capitalize">
              {selectedImage.thirdPartyInfo?.predictions?.[0]?.[0] || 'Unknown'}
            </h3>
            {selectedImage.thirdPartyInfo?.predictions?.[0]?.[1] && (
              <p className="text-gray-600">
                <strong>Diagnosis:</strong> {selectedImage.thirdPartyInfo.predictions[0][1]}
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
