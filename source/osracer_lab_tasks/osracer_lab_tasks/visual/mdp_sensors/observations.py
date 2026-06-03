"""Camera and sensor observation functions for OSRacer visual tasks.

Copied verbatim from WheeledLab visual/mdp_sensors/observations.py — all functions
are robot-agnostic sensor readers. Only the module docstring differs.
"""

from __future__ import annotations

import torch
import torchvision.transforms as transforms
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import Camera
from isaaclab.envs.mdp import *  # noqa: F401, F403

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv

mean = [0.485, 0.456, 0.406]
std = [0.229, 0.224, 0.225]
normalize = transforms.Normalize(mean, std)
grayscale = transforms.Grayscale()
gray_normalize = transforms.Normalize([0.5], [0.5])
gray_transform = transforms.Compose([grayscale, gray_normalize])

color_jitter = transforms.ColorJitter(brightness=0.8, contrast=0.2, saturation=0.8, hue=0.5)
sharpness = transforms.RandomAdjustSharpness(sharpness_factor=2)
gaussian_blur = transforms.GaussianBlur(5, sigma=(0.1, 5.0))


def camera_data_rgb(env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    sensor: Camera = env.scene.sensors[sensor_cfg.name]
    return sensor.data.output["rgb"]


def camera_data_rgb_flattened(env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    sensor: Camera = env.scene.sensors[sensor_cfg.name]
    images = sensor.data.output["rgb"]
    B, H, W, C = images.shape
    images = images[:, H // 3 :, :, :]
    images = images.permute(0, 3, 1, 2).float()
    normalized_imgs = gray_normalize(grayscale(images / 255.0))
    return normalized_imgs.reshape(B, -1)


def camera_data_rgb_flattened_aug(env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    """Crop top third, augment (color jitter + blur), convert to grayscale, flatten."""
    sensor: Camera = env.scene.sensors[sensor_cfg.name]
    images = sensor.data.output["rgb"]
    B, H, W, C = images.shape
    images = images[:, H // 3 :, :, :]
    images = images.permute(0, 3, 1, 2).float() / 255.0
    images = color_jitter(images)
    images = gaussian_blur(images)
    normalized_imgs = gray_normalize(grayscale(images))
    return normalized_imgs.reshape(B, -1)


def camera_data_depth(env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    sensor: Camera = env.scene.sensors[sensor_cfg.name]
    return sensor.data.output["distance_to_image_plane"]


def raycast_depth(env: ManagerBasedEnv, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    sensor: Camera = env.scene.sensors[sensor_cfg.name]
    return sensor.data.output["distance_to_image_plane"]
