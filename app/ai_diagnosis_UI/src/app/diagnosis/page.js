"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Button, Modal, message } from "antd";

import { createProfile } from "@/services/apiService";

const UploadArea = dynamic(() => import("@/components/UploadArea"), { ssr: false });
const ImagePreview = dynamic(() => import("@/components/ImagePreview"), { ssr: false });
const PredictionResult = dynamic(() => import("@/components/PredictionResult"), { ssr: false });
const LoadingSpinner = dynamic(() => import("@/components/LoadingSpinner"), { ssr: false });

const EPHEMERAL_RESULT_KEY = "ai_diagnosis_ephemeral_result";

function clearStoredResult() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(EPHEMERAL_RESULT_KEY);
  }
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`));
    reader.readAsDataURL(file);
  });
}

async function buildPreviewUrls(fileList) {
  const previews = await Promise.all(
    fileList.map(async (fileItem) => ({
      originalname: fileItem.name,
      previewDataUrl: await fileToDataUrl(fileItem.originFileObj),
    }))
  );

  return previews;
}

function attachPreviewUrls(profileResult, previews) {
  if (!profileResult?.profile?.images || !Array.isArray(previews)) {
    return profileResult;
  }

  return {
    ...profileResult,
    profile: {
      ...profileResult.profile,
      images: profileResult.profile.images.map((image, index) => ({
        ...image,
        previewDataUrl:
          previews[index]?.previewDataUrl ??
          previews.find((preview) => preview.originalname === image.originalname)?.previewDataUrl ??
          null,
      })),
    },
  };
}

export default function DiagnosisPage() {
  const [fileList, setFileList] = useState([]);
  const [previewImage, setPreviewImage] = useState("");
  const [isPreviewVisible, setIsPreviewVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const stored = localStorage.getItem(EPHEMERAL_RESULT_KEY);
    if (!stored) {
      return;
    }

    try {
      const parsed = JSON.parse(stored);
      if (parsed?.profile?.persisted === false && Array.isArray(parsed?.profile?.images)) {
        setResult(parsed);
      } else {
        clearStoredResult();
      }
    } catch (error) {
      console.error("Failed to restore local diagnosis result:", error);
      clearStoredResult();
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (result?.profile?.persisted === false) {
      localStorage.setItem(EPHEMERAL_RESULT_KEY, JSON.stringify(result));
    } else if (!result) {
      clearStoredResult();
    }
  }, [result]);

  const handleChange = (info) => {
    setFileList(info.fileList);
    if (info.file.status === "done") {
      message.success(`Upload successful: ${info.file.name}`);
    } else if (info.file.status === "error") {
      message.error(`Upload failed: ${info.file.name}`);
    }
  };

  const handlePreview = (file) => {
    if (typeof window !== "undefined") {
      setPreviewImage(URL.createObjectURL(file.originFileObj));
      setIsPreviewVisible(true);
    }
  };

  const handleRemove = (file) => {
    const updatedFileList = fileList.filter((item) => item.uid !== file.uid);
    setFileList(updatedFileList);
    message.success("File removed");
  };

  const handlePredict = async () => {
    if (fileList.length === 0) {
      message.error("Please upload files first");
      return;
    }

    setLoading(true);

    try {
      const previewUrls = await buildPreviewUrls(fileList);
      const data = await createProfile(fileList);
      const enhancedData = attachPreviewUrls(data, previewUrls);
      setResult(enhancedData);
      message.success("Prediction successful");
    } catch (error) {
      message.error(error.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFileList([]);
    setResult(null);
    clearStoredResult();
    message.info("Files cleared");
  };

  const handleResetResult = () => {
    setResult(null);
    setFileList([]);
    clearStoredResult();
    message.info("Temporary result removed");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="container mx-auto w-full max-w-3xl rounded-lg px-4 py-10 pt-20 text-center">
        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            {result && (
              <PredictionResult
                result={result}
                onReset={handleResetResult}
              />
            )}

            {!result && (
              <>
                <h1 className="fade-in-animation mb-4 text-2xl font-bold text-red-500 sm:text-3xl md:text-4xl">
                  AI-Assisted Diagnosis
                </h1>
                <p className="fade-in-animation mb-8 text-md text-blue-400 sm:text-lg">
                  in Otolaryngological Endoscopy
                </p>
                <UploadArea fileList={fileList} handleChange={handleChange} />
                {fileList.length > 0 && (
                  <ImagePreview
                    fileList={fileList}
                    handlePreview={handlePreview}
                    handleRemove={handleRemove}
                  />
                )}
              </>
            )}
          </>
        )}

        <Modal
          open={isPreviewVisible}
          footer={null}
          onCancel={() => setIsPreviewVisible(false)}
          style={{ backgroundColor: "rgba(0, 0, 0, 0.7)" }}
        >
          <img alt="Preview" className="w-full" src={previewImage} />
        </Modal>

        {!loading && !result && (
          <div className="mt-4 flex justify-center space-x-4">
            <Button
              type="primary"
              onClick={handlePredict}
              disabled={fileList.length === 0}
              className="border-none bg-blue-400 hover:bg-blue-500"
            >
              Predict
            </Button>

            {fileList.length > 0 && (
              <Button
                danger
                onClick={handleClear}
                className="border-none bg-red-500 hover:bg-red-600"
              >
                Clear
              </Button>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .fade-in-animation {
          opacity: 0;
          animation: fadeIn 1.5s ease-in-out forwards;
        }

        @keyframes fadeIn {
          0% {
            opacity: 0;
            transform: translateY(20px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
