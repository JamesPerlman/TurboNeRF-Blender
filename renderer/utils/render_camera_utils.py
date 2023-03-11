import bpy
import math
import numpy as np

from turbo_nerf.utility.math import bl2nerf_mat

from turbo_nerf.utility.pylib import PyTurboNeRF as tn

from turbo_nerf.constants import (
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

def bl2nerf_cam_perspective(blender_camera: bpy.types.Camera, img_dims: tuple[int, int]):
    view_matrix = np.array(blender_camera.matrix_world)

    bl_camera_matrix = tn.Transform4f(view_matrix)

    # look into region_view_3d.view_persepctive
    # get focal length
    fl_x = bl2nerf_fl(blender_camera, img_dims)
    fl_y = fl_x

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
        camera_model = RENDER_CAM_TYPE_PERSPECTIVE

        if RENDER_CAM_TYPE_ID in source:
            camera_model = source[RENDER_CAM_TYPE_ID]
        
        if camera_model not in CAM_TYPE_DECODERS:
            camera_model = RENDER_CAM_TYPE_PERSPECTIVE
        
        decoder = CAM_TYPE_DECODERS[camera_model]
        return decoder(source, img_dims)
    else:
        print(f"INVALID CAMERA SOURCE: {source}")
        return None


CAM_TYPE_DECODERS = {
    RENDER_CAM_TYPE_PERSPECTIVE: bl2nerf_cam_perspective,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: None,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: None,
}
