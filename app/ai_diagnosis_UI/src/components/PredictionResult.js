'use client';

import { useState } from 'react';
import { Button, Card, Form, Input, Modal, Progress } from 'antd';
import { ArrowLeftOutlined, WarningOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { auth } from '@/firebase.config';

function getTopPredictions(image) {
  const topK = Array.isArray(image?.thirdPartyInfo?.top_k)
    ? image.thirdPartyInfo.top_k
        .filter((item) => item && typeof item.label === 'string')
        .map((item) => ({
          label: item.label,
          probability: typeof item.probability === 'number' ? item.probability : null,
        }))
    : [];

  if (topK.length > 0) {
    return topK;
  }

  const legacyPredictions = image?.thirdPartyInfo?.predictions?.[0]?.slice(1) ?? [];
  return legacyPredictions.map((label) => ({
    label,
    probability: null,
  }));
}

function formatProbability(probability) {
  if (typeof probability !== 'number') {
    return 'N/A';
  }

  return `${(probability * 100).toFixed(1)}%`;
}

function getImageSrc(image) {
  return image?.previewDataUrl || image?.path || '';
}

export default function PredictionResult({ result, onReset }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showReportForm, setShowReportForm] = useState(false);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  if (!result || !result.profile || !result.profile.images) {
    return <p>No results available</p>;
  }

  const { images } = result.profile;
  const isEphemeralResult = result.profile?.persisted === false;
  const canReportIssue = Boolean(result.profile?._id && result.profile?.persisted !== false);

  const handleCardClick = (image) => {
    setSelectedImage(image);
    setIsModalOpen(true);
    setShowReportForm(false);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setComment('');
  };

  const handleReportClick = () => {
    if (!canReportIssue) {
      alert('Reporting is unavailable when MongoDB persistence is disabled.');
      return;
    }

    const currentUser = auth?.currentUser;
    if (!currentUser) {
      alert('You need to log in to submit a report.');
      localStorage.setItem('redirectAfterLogin', window.location.pathname);
      router.push('/auth');
      return;
    }

    setShowReportForm(true);
  };

  const handleReportSubmit = async () => {
    if (!comment.trim()) {
      alert('Please fill in the comment field before submitting the report.');
      return;
    }

    try {
      setLoading(true);
      const currentUser = auth?.currentUser;
      if (!currentUser) {
        throw new Error('You need to log in to submit a report.');
      }

      const token = await currentUser.getIdToken();
      const response = await fetch('/api/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          profileId: result.profile._id,
          imageId: selectedImage._id,
          comment: comment.trim(),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert('Your report has been successfully submitted!');
        setShowReportForm(false);
        setComment('');
        setIsModalOpen(false);
      } else {
        alert(data.message || 'Failed to submit the report.');
      }
    } catch (error) {
      console.error('Error submitting report:', error);
      alert('An error occurred while submitting the report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="mb-4 text-4xl font-bold text-red-500">Prediction Results</h1>
      <p className="mb-4 text-lg text-blue-400">Diagnosis based on uploaded images</p>

      <div className={`grid ${images.length === 1 ? 'single-card' : ''}`}>
        {images.map((image, index) => {
          const predictions = getTopPredictions(image);
          const primaryPrediction = predictions[0];

          return (
            <Card
              key={index}
              hoverable
              cover={<img alt={image.originalname} src={getImageSrc(image)} className="h-56 w-full object-cover" />}
              onClick={() => handleCardClick(image)}
              className="relative mx-auto w-full max-w-xs overflow-hidden rounded-2xl border border-red-100 shadow-lg"
            >
              <div className="space-y-3 text-left">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-400">Primary diagnosis</p>
                  <p className="mt-1 text-lg font-semibold text-slate-800">
                    {primaryPrediction?.label || 'No diagnosis available'}
                  </p>
                </div>

                <div className="rounded-xl bg-slate-50 p-3">
                  <div className="flex items-center justify-between text-sm text-slate-600">
                    <span>Confidence</span>
                    <span className="font-semibold text-slate-800">
                      {formatProbability(primaryPrediction?.probability)}
                    </span>
                  </div>
                  {typeof primaryPrediction?.probability === 'number' && (
                    <Progress
                      percent={Number((primaryPrediction.probability * 100).toFixed(1))}
                      showInfo={false}
                      strokeColor="#ef4444"
                      trailColor="#fecaca"
                      className="mt-2"
                    />
                  )}
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-slate-700">Top predictions</p>
                  <div className="space-y-2">
                    {predictions.slice(0, 3).map((prediction) => (
                      <div
                        key={`${image._id}-${prediction.label}`}
                        className="flex items-center justify-between rounded-lg bg-white text-sm text-slate-700"
                      >
                        <span>{prediction.label}</span>
                        <span className="font-medium text-slate-900">
                          {formatProbability(prediction.probability)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="mt-8 text-center">
        <Button
          type="primary"
          icon={<ArrowLeftOutlined />}
          onClick={() => {
            if (typeof onReset === 'function') {
              onReset();
            } else {
              window.location.href = '/diagnosis';
            }
          }}
        >
          Back
        </Button>
      </div>

      <Modal open={isModalOpen} footer={null} onCancel={handleModalClose} width={880}>
        {selectedImage && (
          <div className="modal-content">
            <div className="modal-image">
              <img
                alt={selectedImage.originalname}
                src={getImageSrc(selectedImage)}
                style={{ width: '100%', borderRadius: '10px' }}
              />
            </div>
            <div className="modal-info">
              <h3 className="mb-2 text-2xl font-semibold text-slate-900">
                {getTopPredictions(selectedImage)[0]?.label || 'No diagnosis available'}
              </h3>
              <p className="mb-4 text-sm text-slate-500">
                {selectedImage.originalname}
              </p>

              <div className="space-y-3">
                {getTopPredictions(selectedImage).length > 0 ? (
                  getTopPredictions(selectedImage).map((prediction) => (
                    <div key={`${selectedImage._id}-${prediction.label}`} className="rounded-xl bg-slate-50 p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="font-medium text-slate-800">{prediction.label}</span>
                        <span className="font-semibold text-slate-900">
                          {formatProbability(prediction.probability)}
                        </span>
                      </div>
                      {typeof prediction.probability === 'number' && (
                        <Progress
                          percent={Number((prediction.probability * 100).toFixed(1))}
                          showInfo={false}
                          strokeColor="#2563eb"
                          trailColor="#dbeafe"
                        />
                      )}
                    </div>
                  ))
                ) : (
                  <p>No diagnosis available</p>
                )}
              </div>

              {!canReportIssue ? (
                <p className="mt-4 text-sm text-gray-500">Reporting is disabled in no-DB mode.</p>
              ) : !showReportForm ? (
                <Button icon={<WarningOutlined />} onClick={handleReportClick} className="report-button mt-4">
                  Report Issue
                </Button>
              ) : (
                <Form layout="vertical" style={{ marginTop: '20px' }}>
                  <Form.Item label="Comment">
                    <Input.TextArea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Please provide details about the issue."
                      rows={4}
                    />
                  </Form.Item>
                  <Button
                    type="primary"
                    onClick={handleReportSubmit}
                    loading={loading}
                    style={{ marginTop: '10px' }}
                  >
                    Submit Report
                  </Button>
                </Form>
              )}
            </div>
          </div>
        )}
      </Modal>

      <style jsx>{`
        .grid {
          display: grid;
          grid-template-columns: repeat(1, minmax(0, 1fr));
          justify-items: center;
          gap: 20px;
        }

        .single-card {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100%;
        }

        @media (min-width: 768px) {
          .grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (min-width: 1024px) {
          .grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
        }

        .modal-content {
          display: grid;
          grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
          gap: 24px;
        }

        .modal-image img {
          width: 100%;
          border-radius: 10px;
        }

        .modal-info {
          min-width: 0;
        }

        .report-button {
          background-color: white;
          border: none;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }

        .report-button:hover {
          background-color: #f0f0f0;
        }

        @media (max-width: 767px) {
          .modal-content {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
