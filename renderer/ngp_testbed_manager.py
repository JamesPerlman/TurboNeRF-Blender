from pathlib import Path

import bpy
import numpy as np
from blender_nerf_tools.blender_utility.nerf_render_manager import NeRFRenderManager
import blender_nerf_tools.utility.load_ngp
import pyngp as ngp

from blender_nerf_tools.constants import (
    MASK_BOX_DIMS_ID,
    MASK_CYLINDER_HEIGHT_ID,
    MASK_CYLINDER_RADIUS_ID,
    MASK_FEATHER_ID,
    MASK_MODE_ADD,
    MASK_MODE_ID,
    MASK_MODE_SUBTRACT,
    MASK_OPACITY_ID,
    MASK_TYPE_BOX,
    MASK_TYPE_CYLINDER,
    MASK_TYPE_ID,
    MASK_TYPE_SPHERE,
    MASK_SPHERE_RADIUS_ID,
)
# todo: put into utils file
DEFAULT_NGP_SCALE = 0.33
DEFAULT_NGP_ORIGIN = np.array([0.5, 0.5, 0.5])
def nerf_matrix_to_ngp(nerf_matrix: np.matrix) -> np.matrix:
    result = np.matrix(nerf_matrix)
    result[:, 0:3] *= DEFAULT_NGP_SCALE
    result[:3, 3] = result[:3, 3] * DEFAULT_NGP_SCALE + DEFAULT_NGP_ORIGIN.reshape(3, 1)

    # Cycle axes xyz<-yzx
    result[:3, :] = np.roll(result[:3, :], -1, axis=0)

    return result

__testbed__ = None
def testbed():
    global __testbed__
    if __testbed__ is None:
        __testbed__ = ngp.Testbed(ngp.TestbedMode.Nerf)
        __testbed__.shall_train = False
        __testbed__.fov_axis = 0
    return __testbed__

class NGPTestbedManager(object):
    has_snapshot = False
    @classmethod
    def load_snapshot(cls, snapshot_path: Path):
        cls.has_snapshot = True
        testbed().load_snapshot(str(snapshot_path))

    @classmethod
    def set_camera_matrix(cls, camera_matrix):
        testbed().set_nerf_camera_matrix(camera_matrix)
    
    @classmethod
    def request_render(cls, width, height, mip, callback):
        return testbed().request_nerf_render(
            width=width,
            height=height,
            spp=16,
            linear=True,
            mip=mip,
            flip_y=True,
            masks=cls.get_all_ngp_masks(),
            render_callback=callback
        )
    
    # TODO: abstract
    @classmethod
    def parse_mask(cls, mask):
        NGP_MASK_MODES = {
            MASK_MODE_ADD: ngp.MaskMode.Add,
            MASK_MODE_SUBTRACT: ngp.MaskMode.Subtract,
        }

        mode = NGP_MASK_MODES[mask[MASK_MODE_ID]]
        transform = nerf_matrix_to_ngp(np.matrix(mask.matrix_world))
        opacity = mask[MASK_OPACITY_ID]
        feather = mask[MASK_FEATHER_ID]

        shape = mask[MASK_TYPE_ID]

        print(f"MASK DETIALS: {mode}, {opacity}, {feather}, {shape}")

        if shape == MASK_TYPE_BOX:
            dims = np.array(mask[MASK_BOX_DIMS_ID])
            return ngp.Mask3D.Box(dims, transform, mode, feather, opacity)
        elif shape == MASK_TYPE_CYLINDER:
            r = mask[MASK_CYLINDER_RADIUS_ID]
            h = mask[MASK_CYLINDER_HEIGHT_ID]
            return ngp.Mask3D.Cylinder(r, h, transform, mode, feather, opacity)
        elif shape == MASK_TYPE_SPHERE:
            r = mask[MASK_SPHERE_RADIUS_ID]
            return ngp.Mask3D.Sphere(r, transform, mode, feather, opacity)
    
    @classmethod
    def get_all_ngp_masks(cls):
        masks = NeRFRenderManager.get_all_masks()
        return [cls.parse_mask(mask) for mask in masks]
        
