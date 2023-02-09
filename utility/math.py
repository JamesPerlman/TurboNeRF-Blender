import mathutils
import numpy as np

DEFAULT_NGP_SCALE = 1.0
DEFAULT_NGP_ORIGIN = np.array([0.0, 0.0, 0.0])

def blender_matrix_to_nerf(bl_matrix: np.array, offset, origin, scale) -> np.array:
    result = np.array(bl_matrix)
    result[:, 1:3] *= -1
    result[:3, 3] = (result[:3, 3] + offset) * scale + origin
    result[:3, :] = np.roll(result[:3, :], -1, axis=0)
    return result

def nerf_matrix_to_blender(nerf_matrix: np.array, offset, origin, scale) -> np.array:
    result = np.array(nerf_matrix)
    result[:3, :] = np.roll(result[:3, :], 1, axis=0)
    result[:3, 3] = (result[:3, 3] - origin) / scale - offset
    result[:, 1:3] *= -1
    return result

def bl2nerf_mat(bl_matrix: mathutils.Matrix, offset = np.array([0.0, 0.0, 0.0]), origin = DEFAULT_NGP_ORIGIN, scale = DEFAULT_NGP_SCALE) -> np.array:
    return nerf_matrix_to_blender(np.array(bl_matrix), offset, origin, scale)

def nerf2bl_mat(nrc_matrix: np.array, offset = np.array([0.0, 0.0, 0.0]), origin = DEFAULT_NGP_ORIGIN, scale = DEFAULT_NGP_SCALE) -> mathutils.Matrix:
    return mathutils.Matrix(blender_matrix_to_nerf(nrc_matrix, offset, origin, scale))

def bl2nerf_pos(
        xyz: np.array,
        origin = DEFAULT_NGP_ORIGIN,
        scale = DEFAULT_NGP_SCALE
    ) -> np.array:
    xyz_cycled = np.array([xyz[1], xyz[2], xyz[0]])
    return scale * xyz_cycled + origin
