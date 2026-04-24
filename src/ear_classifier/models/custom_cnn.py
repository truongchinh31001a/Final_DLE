from __future__ import annotations

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class CustomCNN(nn.Module):
    def __init__(
        self,
        num_classes: int,
        dropout: float = 0.3,
        head_hidden_dim: int = 128,
        channels: tuple[int, int, int, int] = (32, 64, 128, 256),
    ) -> None:
        super().__init__()
        c1, c2, c3, c4 = channels
        self.features = nn.Sequential(
            ConvBlock(3, c1),
            ConvBlock(c1, c2),
            ConvBlock(c2, c3),
            ConvBlock(c3, c4),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.BatchNorm1d(c4),
            nn.Dropout(dropout),
            nn.Linear(c4, head_hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(head_hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)
