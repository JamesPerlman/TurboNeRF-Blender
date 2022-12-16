import mathutils
import numpy as np

DEFAULT_NGP_SCALE = 1.0
DEFAULT_NGP_ORIGIN = np.array([0.0, 0.0, 0.0])

def nerf_matrix_to_ngp(nerf_matrix: np.array, offset, origin, scale) -> np.array:
    result = np.array(nerf_matrix)
    result[:, 1:3] *= -1
    result[:3, 3] = (result[:3, 3] + offset) * scale + origin
    # Cycle axes xyz<-yzx
    result[:3, :] = np.roll(result[:3, :], -1, axis=0)
    return result

def ngp_matrix_to_nerf(ngp_matrix: np.array, offset, origin, scale) -> np.array:
    result = np.array(ngp_matrix)
    result[:3, :] = np.roll(result[:3, :], 1, axis=0)
    result[:3, 3] = (result[:3, 3] - origin) / scale - offset
    result[:, 1:3] *= -1
    return result

def bl2ngp_mat(bl_matrix: mathutils.Matrix, offset = np.array([0.0, 0.0, 0.0]), origin = DEFAULT_NGP_ORIGIN, scale = DEFAULT_NGP_SCALE) -> np.array:
    return nerf_matrix_to_ngp(np.array(bl_matrix), offset, origin, scale)

def ngp2bl_mat(ngp_matrix: np.array, offset = np.array([0.0, 0.0, 0.0]), origin = DEFAULT_NGP_ORIGIN, scale = DEFAULT_NGP_SCALE) -> mathutils.Matrix:
    return mathutils.Matrix(ngp_matrix_to_nerf(ngp_matrix, offset, origin, scale))

def bl2ngp_pos(
        xyz: np.array,
        origin = DEFAULT_NGP_ORIGIN,
        scale = DEFAULT_NGP_SCALE
    ) -> np.array:
    xyz_cycled = np.array([xyz[1], xyz[2], xyz[0]])
    return scale * xyz_cycled + origin
