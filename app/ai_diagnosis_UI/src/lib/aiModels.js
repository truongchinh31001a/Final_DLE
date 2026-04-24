export const AI_MODEL_STORAGE_KEY = 'ai_diagnosis_selected_model';
export const DEFAULT_AI_MODEL_ID = 'baseline_effb0';

export const AI_MODEL_OPTIONS = [
  {
    value: 'baseline_effb0',
    label: 'EfficientNet-B0',
    checkpoint: 'models/checkpoints/baseline_effb0/best.pt',
  },
  {
    value: 'baseline_resnet18',
    label: 'ResNet18',
    checkpoint: 'models/checkpoints/baseline_resnet18/best.pt',
  },
  {
    value: 'baseline_custom_cnn',
    label: 'Custom CNN',
    checkpoint: 'models/checkpoints/baseline_custom_cnn/best.pt',
  },
];

export function isValidAIModelId(modelId) {
  return AI_MODEL_OPTIONS.some((option) => option.value === modelId);
}

export function resolveAIModelCheckpoint(modelId) {
  const selectedOption = AI_MODEL_OPTIONS.find((option) => option.value === modelId);
  return selectedOption?.checkpoint ?? AI_MODEL_OPTIONS[0].checkpoint;
}

export function getAIModelLabel(modelId) {
  const selectedOption = AI_MODEL_OPTIONS.find((option) => option.value === modelId);
  return selectedOption?.label ?? AI_MODEL_OPTIONS[0].label;
}
