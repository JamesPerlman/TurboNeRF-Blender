import bpy
import math
import numpy as np

from blender_nerf_tools.utility.math import bl2nerf_mat

from blender_nerf_tools.utility.pylib import PyTurboNeRF as tn

from blender_nerf_tools.constants import (
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON
)


def bl2nerf_fl(blender_camera: bpy.types.Object, output_dimensions: tuple[int, int]) -> float:
    cam_data = blender_camera.data
    (nerf_w, nerf_h) = output_dimensions
    # calculate focal len
    bl_sw = cam_data.sensor_width
    bl_sh = cam_data.sensor_height
    bl_f  = cam_data.lens

    # get blender sensor size in pixels
    px_w: float
    # px_h: float
    
    if cam_data.sensor_fit == 'AUTO':
        bl_asp = 1.0
        nerf_asp = nerf_h / nerf_w

        if nerf_asp > bl_asp:
            px_w = nerf_h / bl_asp
            # px_h = nerf_h
        else:
            px_w = nerf_w
            # px_h = nerf_w * bl_asp

    elif cam_data.sensor_fit == 'HORIZONTAL':
        px_w = nerf_w
        # px_h = nerf_w * bl_sh / bl_sw

    elif cam_data.sensor_fit == 'VERTICAL':
        px_w = nerf_h * bl_sw / bl_sh
        # px_h = nerf_h
    
    
    # focal length in pixels
    px_f = bl_f / bl_sw * px_w

    return px_f

# converts aperture fstop to aperture size
def bl2nerf_fstop2size(fstop: float) -> float:
    return 1.0 / (2.0 * fstop)

def bl2nerf_cam_regionview3d(region_view_3d: bpy.types.RegionView3D, img_dims: tuple[int, int]):
    # P
    projection_matrix = np.array(region_view_3d.window_matrix)
    # V 
    view_matrix = np.array(region_view_3d.view_matrix.inverted())
    # P * V
    perspective_matrix = np.array(region_view_3d.perspective_matrix)

    bl_camera_matrix = tn.Transform4f(view_matrix)

    is_perspective = region_view_3d.is_perspective

    # look into region_view_3d.view_persepctive
    # get focal length
    fl_x = 0.5 * img_dims[0] * projection_matrix[0, 0]
    fl_y = 0.5 * img_dims[1] * projection_matrix[1, 1]

    view_angle_x = 2.0 * math.atan2(0.5 * img_dims[0], fl_x)
    view_angle_y = 2.0 * math.atan2(0.5 * img_dims[1], fl_y)

    return tn.Camera(
        resolution=img_dims,
        near=0.1,
        far=10.0,
        focal_length=(fl_x, fl_y),
        view_angle=(view_angle_x, view_angle_y),
        transform=bl_camera_matrix.from_nerf()
    )

def bl2nerf_cam(source: bpy.types.RegionView3D | bpy.types.Object, img_dims: tuple[int, int]):
    if isinstance(source, bpy.types.RegionView3D):
        return bl2nerf_cam_regionview3d(source, img_dims)
    elif isinstance(source, bpy.types.Object):
        camera_model = source[RENDER_CAM_TYPE_ID]
        decoder = CAM_TYPE_DECODERS[camera_model]
        return decoder(source, img_dims)
    else:
        print(f"INVALID CAMERA SOURCE: {source}")
        return None


CAM_TYPE_DECODERS = {
    RENDER_CAM_TYPE_PERSPECTIVE: bl2nerf_cam,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: None,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: None,
}

class NeRFRenderCamera:

    focal_length: float
    transform: np.ndarray

    def __init__(self, source: bpy.types.RegionView3D | bpy.types.Camera, dimensions: tuple[int, int]):
        if isinstance(source, bpy.types.RegionView3D):
            self._init_from_region_view_3d(source, dimensions)
        elif isinstance(source, bpy.types.Camera):
            self._init_from_camera(source)
    
    def _init_from_camera(self, camera: bpy.types.Camera):
        pass

    def _init_from_region_view_3d(self, region_view_3d: bpy.types.RegionView3D, dimensions: tuple[int, int]):
        # P
        projection_matrix = np.array(region_view_3d.window_matrix)
        # V 
        view_matrix = np.array(region_view_3d.view_matrix.inverted())
        # P * V
        perspective_matrix = np.array(region_view_3d.perspective_matrix)

        is_perspective = region_view_3d.is_perspective

        # look into region_view_3d.view_persepctive
        # get focal length
        self.focal_length = 0.5 * dimensions[0] * projection_matrix[0, 0]
        self.transform = view_matrix[:3, :4]
    
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, tn.Camera):
            return False
        return self.focal_length == __o.focal_length and np.array_equal(self.transform, __o.transform)
    
    def __ne__(self, __o: object) -> bool:
        if not isinstance(__o, tn.Camera):
            return True
        
        return not self.__eq__(__o)
