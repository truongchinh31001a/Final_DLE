import fs from 'fs';
import FormData from 'form-data';
import fetch from 'node-fetch';

import {
  DEFAULT_AI_MODEL_ID,
  getAIModelLabel,
  isValidAIModelId,
} from '@/lib/aiModels';

const DEFAULT_AI_API_URL = 'http://127.0.0.1:8000/predict';
const DEFAULT_MODALITY = 'ear';

function toLegacyPredictions(result) {
  const labels = Array.isArray(result?.top_k)
    ? result.top_k.map((item) => item?.label).filter(Boolean)
    : [];
  const primaryLabel = typeof result?.label === 'string' ? result.label : labels[0];
  const orderedLabels = [];

  for (const label of [primaryLabel, ...labels]) {
    if (label && !orderedLabels.includes(label)) {
      orderedLabels.push(label);
    }
  }

  return orderedLabels.length > 0 ? [[DEFAULT_MODALITY, ...orderedLabels]] : [];
}

function normalizeAIResult(result) {
  if (result?.predictions) {
    return result;
  }

  return {
    predictions: toLegacyPredictions(result),
    label: result?.label ?? null,
    confidence: typeof result?.confidence === 'number' ? result.confidence : null,
    top_k: Array.isArray(result?.top_k) ? result.top_k : [],
  };
}

export const sendImageToThirdPartyAPI = async (filePath, modelId = DEFAULT_AI_MODEL_ID) => {
  try {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    const normalizedModelId = isValidAIModelId(modelId) ? modelId : DEFAULT_AI_MODEL_ID;
    const apiUrl = new URL(process.env.API_URL_AI || DEFAULT_AI_API_URL);
    apiUrl.searchParams.set('model_id', normalizedModelId);

    const response = await fetch(apiUrl.toString(), {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to send image to third-party API. Status: ${response.status}`);
    }

    const result = await response.json();
    return {
      ...normalizeAIResult(result),
      model: {
        id: normalizedModelId,
        label: getAIModelLabel(normalizedModelId),
      },
    };
  } catch (error) {
    console.error('Error sending image to third-party API:', error.message);
    throw new Error(error.message);
  }
};
