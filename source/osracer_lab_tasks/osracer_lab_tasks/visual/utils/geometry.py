"""Procedural colored-plane terrain generation — inlined from WheeledLab."""

import os
import numpy as np
from scipy.ndimage import binary_dilation
from pxr import Usd, UsdGeom, UsdPhysics, Gf

from .traversability_utils import TraversabilityHashmapUtil


def _generated_colored_plane(map_size, spacing, env_size, sub_group_size, num_walkers, color_sampling):
    num_rows, num_cols = map_size
    row_spacing, col_spacing = spacing
    env_num_rows, env_num_cols = env_size

    width = num_rows * row_spacing
    height = num_cols * col_spacing

    if num_rows % env_num_rows != 0 or num_cols % env_num_cols != 0:
        raise ValueError("Map size must be a multiple of the sub environment size.")

    num_env_rows = num_rows // env_num_rows
    num_env_cols = num_cols // env_num_cols

    xs = np.linspace(-width / 2, width / 2, num_rows) - row_spacing / 2
    ys = np.linspace(-height / 2, height / 2, num_cols) - col_spacing / 2
    xx, yy = np.meshgrid(xs, ys)

    vertices = [(x, y, 0) for x, y in zip(xx.ravel(), yy.ravel())]

    def color_sampler(r, g, b, rng):
        r = np.random.uniform(r - rng // 2, r + rng // 2) / 255.0
        g = np.random.uniform(g - rng // 2, g + rng // 2) / 255.0
        b = np.random.uniform(b - rng // 2, b + rng // 2) / 255.0
        return Gf.Vec3f(r, g, b)

    if color_sampling:
        colors = [color_sampler(30, 30, 30, 30), color_sampler(220, 220, 220, 30)]
    else:
        colors = [Gf.Vec3f(0.0, 0.0, 0.0), Gf.Vec3f(1.0, 1.0, 1.0)]

    faces = []
    face_counts = []
    traversability_hashmap = np.zeros((num_rows, num_cols)).astype(bool)

    for row_index in range(num_rows - 1):
        for col_index in range(num_cols - 1):
            v0 = row_index * num_cols + col_index
            v1 = v0 + 1
            v2 = v0 + num_cols
            v3 = v2 + 1
            faces += [v0, v1, v2, v2, v1, v3]
            face_counts += [3, 3]

    for i in range(num_env_rows):
        for j in range(num_env_cols):
            sr, er = i * env_num_rows, (i + 1) * env_num_rows
            sc, ec = j * env_num_cols, (j + 1) * env_num_cols
            traversability_hashmap[sr:er, sc:ec] = _generate_env_map(env_size, sub_group_size, num_walkers)

    dilate_structure = np.array([[0, 1, 0], [0, 1, 1], [0, 0, 0]]).astype(bool)
    traversability_hashmap = binary_dilation(traversability_hashmap, structure=dilate_structure, iterations=1)

    face_colors_tri = []
    for ri in range(num_rows - 1):
        for ci in range(num_cols - 1):
            c = colors[int(traversability_hashmap[ri, ci])]
            face_colors_tri += [c, c]

    return vertices, faces, face_counts, face_colors_tri, traversability_hashmap


def _generate_env_map(env_size, sub_group_size, num_walkers):
    env_num_rows, env_num_cols = env_size
    group_num_rows, group_num_cols = sub_group_size

    traversability_hashmap = np.zeros((env_num_rows, env_num_cols)).astype(bool)
    start_points = []
    for i in range(env_num_rows // group_num_rows):
        for j in range(env_num_cols // group_num_cols):
            sr = np.random.randint(0, group_num_rows) + i * group_num_rows
            sc = np.random.randint(0, group_num_cols) + j * group_num_cols
            start_points.append((sr, sc))

    for start_row, start_col in start_points:
        for _ in range(num_walkers):
            end_row = np.random.randint(0, env_num_rows)
            end_col = np.random.randint(0, env_num_cols)
            while traversability_hashmap[end_row, end_col]:
                end_row = np.random.randint(0, env_num_rows)
                end_col = np.random.randint(0, env_num_cols)
            _generate_path(start_row, start_col, end_row, end_col, traversability_hashmap)

    return traversability_hashmap


def _generate_path(start_row, start_col, end_row, end_col, traversability_hashmap):
    r, c = start_row, start_col
    traversability_hashmap[r, c] = True

    row_action = "up" if end_row < r else "down"
    col_action = "left" if end_col < c else "right"
    seq = [row_action] * abs(end_row - r) + [col_action] * abs(end_col - c)
    seq = np.random.permutation(seq)

    for action in seq:
        traversability_hashmap[r, c] = True
        if action == "up":
            r -= 1
        elif action == "down":
            r += 1
        elif action == "left":
            c -= 1
        elif action == "right":
            c += 1
        traversability_hashmap[r, c] = True


def create_geometry(file_path, map_size, spacing, env_size, sub_group_size, num_walkers=16, color_sampling=False):
    """Create a USD file with a traversable colored-plane terrain."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    stage = Usd.Stage.CreateNew(file_path)
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.LinearUnits.meters)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    xform = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(xform.GetPrim())

    plane = UsdGeom.Mesh.Define(stage, "/World/colored_plane")
    vertices, faces, face_counts, face_colors, traversability_hashmap = _generated_colored_plane(
        map_size, spacing, env_size, sub_group_size, num_walkers, color_sampling
    )
    plane.GetPointsAttr().Set(vertices)
    plane.GetFaceVertexCountsAttr().Set(face_counts)
    plane.GetFaceVertexIndicesAttr().Set(faces)
    plane.CreateDisplayColorPrimvar(UsdGeom.Tokens.uniform).Set(face_colors)

    UsdPhysics.MeshCollisionAPI.Apply(xform.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(plane.GetPrim())
    UsdPhysics.CollisionGroup.Define(stage, "/World/colored_plane/collision_group")

    stage.GetRootLayer().Save()

    traversability_list = traversability_hashmap.tolist()
    TraversabilityHashmapUtil().set_traversability_hashmap(traversability_list, map_size, spacing)
    return traversability_list


def generate_random_poses(num_poses, row_spacing, col_spacing, traversability_hashmap, margin=0.1):
    """Sample random traversable poses from the hashmap."""
    H, W = len(traversability_hashmap), len(traversability_hashmap[0])
    arr = np.array(traversability_hashmap)
    candidates = arr.nonzero()
    idxs = np.random.choice(len(candidates[0]), num_poses)
    ys, xs = candidates[0][idxs], candidates[1][idxs]
    poses = []
    for i in range(len(xs)):
        x = (float(xs[i]) - W // 2) * row_spacing
        y = (float(ys[i]) - H // 2) * col_spacing
        angle = np.random.uniform(0, 360.0)
        poses.append((x, y, angle))
    return poses
