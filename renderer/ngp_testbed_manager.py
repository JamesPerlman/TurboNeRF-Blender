from pathlib import Path

import bpy
import mathutils
import numpy as np
from blender_nerf_tools.blender_utility.nerf_render_manager import NeRFRenderManager
from blender_nerf_tools.blender_utility.render_camera_utility import get_camera_focal_length
from blender_nerf_tools.renderer.nerf_snapshot_manager import NeRFSnapshotManager
import blender_nerf_tools.utility.load_ngp
from blender_nerf_tools.utility.ngp_math import bl2ngp_mat, bl2ngp_pos

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
    SNAPSHOT_AABB_CENTER_ID,
    SNAPSHOT_AABB_SIZE_ID,
    SNAPSHOT_OPACITY_ID,
    SNAPSHOT_PATH_ID,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
)

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
    active_camera = {}
    
    @classmethod
    def request_render(cls, camera, width, height, mip, callback=None):
        render_request = cls.create_render_request(camera, width, height, mip)
        if callback is None:
            return testbed().request_nerf_render_sync(render_request)
        else:
            testbed().request_nerf_render_async(render_request, callback)
    
    # TODO: abstract
    @classmethod
    def parse_mask(cls, mask):
        NGP_MASK_MODES = {
            MASK_MODE_ADD: ngp.MaskMode.Add,
            MASK_MODE_SUBTRACT: ngp.MaskMode.Subtract,
        }

        mode = NGP_MASK_MODES[mask[MASK_MODE_ID]]
        transform = bl2ngp_mat(mask.matrix_local)
        opacity = mask[MASK_OPACITY_ID]
        feather = mask[MASK_FEATHER_ID]

        shape = mask[MASK_TYPE_ID]

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
    def get_masks_ngp(cls, parent=None):
        masks = NeRFRenderManager.get_all_masks()
        return [cls.parse_mask(mask) for mask in masks if mask.parent == parent]
    
    @classmethod
    def get_all_ngp_nerfs(cls):
        snapshots = NeRFSnapshotManager.get_all_snapshots()

        # TODO: abstract
        def get_snapshot_ngp_bbox(snapshot):
            aabb_center = snapshot[SNAPSHOT_AABB_CENTER_ID]
            aabb_size = snapshot[SNAPSHOT_AABB_SIZE_ID]
            
            bbox = ngp.BoundingBox(
                bl2ngp_pos(
                    np.array([
                        aabb_center[0] - aabb_size[0] / 2,
                        aabb_center[1] - aabb_size[1] / 2,
                        aabb_center[2] - aabb_size[2] / 2,
                    ]),
                ),
                bl2ngp_pos(
                    np.array([
                        aabb_center[0] + aabb_size[0] / 2,
                        aabb_center[1] + aabb_size[1] / 2,
                        aabb_center[2] + aabb_size[2] / 2,
                    ])
                )
            )
            return bbox
        
        # TODO: figure out why we need this
        bl_rot = np.array([
            [0, 0, 1, 0],
            [-1, 0, 0, 0],
            [0, -1, 0, 0],
            [0, 0, 0, 1],
        ])

        nerfs = [
            ngp.NerfDescriptor(
                snapshot_path_str=s[SNAPSHOT_PATH_ID],
                aabb=get_snapshot_ngp_bbox(s),
                transform=np.matmul(bl2ngp_mat(s.matrix_world, origin=[0.0, 0.0, 0.0]), bl_rot),
                modifiers=ngp.RenderModifiers(masks=[mask for mask in cls.get_masks_ngp(parent=s)]),
                opacity=s[SNAPSHOT_OPACITY_ID],
            ) for s in snapshots]
        return nerfs

    @classmethod
    def create_render_request(cls, camera, width, height, mip):
        resolution = np.array([width, height])
        ds = ngp.DownsampleInfo.MakeFromMip(resolution, mip)
        
        output = ngp.RenderOutputProperties(
            resolution=resolution,
            ds=ds,
            spp=1,
            color_space=ngp.ColorSpace.SRGB,
            tonemap_curve=ngp.TonemapCurve.Identity,
            exposure=0.0,
            background_color=np.array([0.0, 0.0, 0.0, 0.0]),
            flip_y=True,
        )

        nerfs = cls.get_all_ngp_nerfs()

        aabb = ngp.BoundingBox(
            np.array([-4, -8, -8]),
            np.array([8, 8, 8]),
        )
        render_modifiers = ngp.RenderModifiers(masks=cls.get_masks_ngp(parent=None))
        render_request = ngp.RenderRequest(output=output, camera=camera, modifiers=render_modifiers, nerfs=nerfs, aabb=aabb)
        return render_request


