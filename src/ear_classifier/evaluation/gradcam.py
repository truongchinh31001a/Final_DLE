from __future__ import annotations

import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.activations: torch.Tensor | None = None
        self.gradients: torch.Tensor | None = None
        self._handles = [
            target_layer.register_forward_hook(self._save_activation),
            target_layer.register_full_backward_hook(self._save_gradient),
        ]

    def _save_activation(self, _module, _inputs, output) -> None:
        self.activations = output.detach()

    def _save_gradient(self, _module, _grad_input, grad_output) -> None:
        self.gradients = grad_output[0].detach()

    def remove_hooks(self) -> None:
        for handle in self._handles:
            handle.remove()

    def __call__(self, image_batch: torch.Tensor, class_idx: int | None = None) -> torch.Tensor:
        self.model.zero_grad(set_to_none=True)
        logits = self.model(image_batch)
        if class_idx is None:
            class_idx = int(logits.argmax(dim=1).item())
        score = logits[:, class_idx].sum()
        score.backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError("GradCAM hooks did not capture activations/gradients.")

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = F.interpolate(cam, size=image_batch.shape[-2:], mode="bilinear", align_corners=False)
        cam_min = cam.amin(dim=(2, 3), keepdim=True)
        cam_max = cam.amax(dim=(2, 3), keepdim=True)
        return (cam - cam_min) / (cam_max - cam_min + 1e-8)

