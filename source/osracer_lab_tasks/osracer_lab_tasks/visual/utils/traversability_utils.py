"""Traversability hashmap util — inlined from WheeledLab."""

import torch


class TraversabilityHashmapUtil:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.traversability_hashmap = None
            self.num_plots = 0

    def set_traversability_hashmap(self, traversability_hashmap, map_size, spacing):
        self.num_rows, self.num_cols = map_size
        self.row_spacing, self.col_spacing = spacing
        self.traversability_hashmap = traversability_hashmap
        self.width = self.num_rows * self.row_spacing
        self.height = self.num_cols * self.col_spacing
        self.device = None

    def get_traversability(self, poses: torch.Tensor):
        if self.traversability_hashmap is None:
            return torch.ones(poses.shape[0], device=poses.device)

        if self.device is None:
            self.traversability_hashmap = torch.tensor(self.traversability_hashmap, device=poses.device)
            self.device = poses.device

        xs, ys = poses[:, 0], poses[:, 1]
        x_idx, y_idx = self.get_map_id(xs, ys)
        return self.traversability_hashmap[y_idx, x_idx]

    def get_map_id(self, x, y):
        x_idx = ((x + self.width / 2.0 + self.row_spacing / 2.0) / self.row_spacing).long()
        y_idx = ((y + self.height / 2 + self.col_spacing / 2) / self.col_spacing).long()
        x_idx = torch.clamp(x_idx, 0, self.num_rows - 1)
        y_idx = torch.clamp(y_idx, 0, self.num_cols - 1)
        return x_idx, y_idx
