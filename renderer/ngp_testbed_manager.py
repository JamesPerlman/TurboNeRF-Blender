from pathlib import Path

import bpy
import mathutils
import numpy as np
from blender_nerf_tools.blender_utility.nerf_render_manager import NeRFRenderManager
from blender_nerf_tools.blender_utility.render_camera_utility import get_camera_focal_length
from blender_nerf_tools.renderer.nerf_snapshot_manager import NeRFSnapshotManager
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
    SNAPSHOT_AABB_CENTER_ID,
    SNAPSHOT_AABB_SIZE_ID,
    SNAPSHOT_PATH_ID,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
)
# todo: put into utils file
DEFAULT_NGP_SCALE = 0.33
DEFAULT_NGP_ORIGIN = np.array([0.5, 0.5, 0.5])

def nerf_matrix_to_ngp(nerf_matrix: np.array, offset, origin, scale) -> np.array:
    result = np.array(nerf_matrix)
    return result
    # result[:, 1:3] *= -1
    # result[:3, 3] = (result[:3, 3] + offset) * scale + origin
    # # Cycle axes xyz<-yzx
    # result[:3, :] = np.roll(result[:3, :], -1, axis=0)
    # return result

def bl2ngp_mat(bl_matrix: mathutils.Matrix, offset = np.array([0.0, 0.0, 0.0]), origin = DEFAULT_NGP_ORIGIN, scale = DEFAULT_NGP_SCALE) -> np.array:
    return np.array(bl_matrix)
    # return nerf_matrix_to_ngp(np.array(bl_matrix), offset, origin, scale)

def bl2ngp_pt(
        xyz: np.array,
        origin = DEFAULT_NGP_ORIGIN,
        scale = DEFAULT_NGP_SCALE
    ) -> np.array:
    return xyz
    # xyz_cycled = np.array([xyz[1], xyz[2], xyz[0]])
    # return scale * xyz_cycled + origin

RENDER_CAM_TYPE_TO_NGP_CAM_MODEL = {
    RENDER_CAM_TYPE_PERSPECTIVE: ngp.CameraModel.Perspective,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: ngp.CameraModel.SphericalQuadrilateral,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: ngp.CameraModel.QuadrilateralHexahedron,
}

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
    def request_render(cls, camera, width, height, mip, callback):
        return testbed().request_nerf_render(
            render_request=cls.create_render_request(camera, width, height, mip),
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
        transform = bl2ngp_mat(mask.matrix_world)
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
    
    @classmethod
    def get_all_ngp_nerfs(cls):
        snapshots = NeRFSnapshotManager.get_all_snapshots()
        
        # TODO: abstract
        def get_snapshot_ngp_bbox(snapshot):
            aabb_center = snapshot[SNAPSHOT_AABB_CENTER_ID]
            aabb_size = snapshot[SNAPSHOT_AABB_SIZE_ID]
            
            bbox = ngp.BoundingBox(
                bl2ngp_pt(
                    np.array([
                        aabb_center[0] - aabb_size[0] / 2,
                        aabb_center[1] - aabb_size[1] / 2,
                        aabb_center[2] - aabb_size[2] / 2,
                    ])
                ),
                bl2ngp_pt(
                    np.array([
                        aabb_center[0] + aabb_size[0] / 2,
                        aabb_center[1] + aabb_size[1] / 2,
                        aabb_center[2] + aabb_size[2] / 2,
                    ])
                ),
            )
            return bbox

        nerfs = [
            ngp.NerfDescriptor(
                snapshot_path_str=s[SNAPSHOT_PATH_ID],
                aabb=get_snapshot_ngp_bbox(s),
                transform=s.matrix_world,
                modifiers=ngp.RenderModifiers(masks=[]),
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

        fl = camera.focal_length
        print("focal len: ", fl)
        camera = ngp.RenderCameraProperties(
            transform=bl2ngp_mat(camera.transform)[:-1, :],
            model=ngp.CameraModel.Perspective, # RENDER_CAM_TYPE_TO_NGP_CAM_MODEL[camera[RENDER_CAM_TYPE_ID]],
            focal_length=fl,
            near_distance=0.0,
            aperture_size=0.0,
            focus_z=1.0,
            spherical_quadrilateral=ngp.SphericalQuadrilateralConfig.Zero(),
            quadrilateral_hexahedron=ngp.QuadrilateralHexahedronConfig.Zero(),
        )

        nerfs = cls.get_all_ngp_nerfs()

        aabb = ngp.BoundingBox(
            bl2ngp_pt(np.array([-4, -8, -8])),
            bl2ngp_pt(np.array([8, 8, 8])),
        )
        render_modifiers = ngp.RenderModifiers(masks=cls.get_all_ngp_masks())

        render_request = ngp.RenderRequest(output=output, camera=camera, modifiers=render_modifiers, nerfs=nerfs, aabb=aabb)
        return render_request


