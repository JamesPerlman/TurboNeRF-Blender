import bpy
import numpy as np
from blender_nerf_tools.utility.ngp_math import bl2ngp_mat

import pyngp as ngp

from blender_nerf_tools.constants import (
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON
)


RENDER_CAM_TYPE_TO_NGP_CAM_MODEL = {
    RENDER_CAM_TYPE_PERSPECTIVE: ngp.CameraModel.Perspective,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: ngp.CameraModel.SphericalQuadrilateral,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: ngp.CameraModel.QuadrilateralHexahedron,
}

# c++ class:
# CameraProperties(
#     const Eigen::Matrix<float, 3, 4>& transform,
#     ECameraModel model,
#     float focal_length,
#     float near_distance,
#     float aperture_size,
#     float focus_z,
#     const SphericalQuadrilateral& spherical_quadrilateral,
#     const QuadrilateralHexahedron& quadrilateral_hexahedron
# )

def bl2ngp_fl(blender_camera: bpy.types.Object, output_dimensions: tuple[int, int]) -> float:
    cam_data = blender_camera.data
    (ngp_w, ngp_h) = output_dimensions
    # calculate focal len
    bl_sw = cam_data.sensor_width
    bl_sh = cam_data.sensor_height
    bl_f  = cam_data.lens

    # get blender sensor size in pixels
    px_w: float
    # px_h: float
    
    if cam_data.sensor_fit == 'AUTO':
        bl_asp = 1.0
        ngp_asp = ngp_h / ngp_w

        if ngp_asp > bl_asp:
            px_w = ngp_h / bl_asp
            # px_h = ngp_h
        else:
            px_w = ngp_w
            # px_h = ngp_w * bl_asp

    elif cam_data.sensor_fit == 'HORIZONTAL':
        px_w = ngp_w
        # px_h = ngp_w * bl_sh / bl_sw

    elif cam_data.sensor_fit == 'VERTICAL':
        px_w = ngp_h * bl_sw / bl_sh
        # px_h = ngp_h
    
    
    # focal length in pixels
    px_f = bl_f / bl_sw * px_w

    return px_f

# converts aperture fstop to aperture size
def bl2ngp_fstop2size(fstop: float) -> float:
    return 1.0 / (2.0 * fstop)

def bl2ngp_cam_perspective(camera: bpy.types.Object, output_dims: tuple[int, int]) -> ngp.RenderCameraProperties:
    aperture_size = 0.0
    if camera.data.dof.use_dof:
        aperture_size = bl2ngp_fstop2size(camera.data.dof.aperture_fstop)
    
    return ngp.RenderCameraProperties(
        transform=bl2ngp_mat(camera.matrix_world)[:-1, :],
        model=ngp.CameraModel.Perspective,
        focal_length=bl2ngp_fl(camera, output_dims),
        near_distance=camera.data.clip_start,
        aperture_size=aperture_size,
        focus_z=camera.data.dof.focus_distance,
        spherical_quadrilateral=ngp.SphericalQuadrilateralConfig.Zero(),
        quadrilateral_hexahedron=ngp.QuadrilateralHexahedronConfig.Zero(),
    )

def bl2ngp_cam_regionview3d(region_view_3d: bpy.types.RegionView3D, img_dims: tuple[int, int]) -> ngp.RenderCameraProperties:
    # P
        projection_matrix = np.array(region_view_3d.window_matrix)
        # V 
        view_matrix = np.array(region_view_3d.view_matrix.inverted())
        # P * V
        perspective_matrix = np.array(region_view_3d.perspective_matrix)

        is_perspective = region_view_3d.is_perspective

        # look into region_view_3d.view_persepctive
        # get focal length
        focal_length = 0.5 * img_dims[0] * projection_matrix[0, 0]

        return ngp.RenderCameraProperties(
            transform=bl2ngp_mat(view_matrix)[:-1, :],
            model=ngp.CameraModel.Perspective, # RENDER_CAM_TYPE_TO_NGP_CAM_MODEL[camera[RENDER_CAM_TYPE_ID]],
            focal_length=focal_length,
            near_distance=0.0,
            aperture_size=0.0,
            focus_z=1.0,
            spherical_quadrilateral=ngp.SphericalQuadrilateralConfig.Zero(),
            quadrilateral_hexahedron=ngp.QuadrilateralHexahedronConfig.Zero(),
        )

CAM_TYPE_DECODERS = {
    RENDER_CAM_TYPE_PERSPECTIVE: bl2ngp_cam_perspective,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: None,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: None,
}

def bl2ngp_cam(source: bpy.types.RegionView3D | bpy.types.Object, img_dims: tuple[int, int]) -> ngp.RenderCameraProperties:
    if isinstance(source, bpy.types.RegionView3D):
        return bl2ngp_cam_regionview3d(source, img_dims)
    elif isinstance(source, bpy.types.Object):
        camera_model = source[RENDER_CAM_TYPE_ID]
        decoder = CAM_TYPE_DECODERS[camera_model]
        return decoder(source, img_dims)
    else:
        print(f"INVALID CAMERA SOURCE: {source}")
        return None

class NGPRenderCamera:

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
        self.transform = view_matrix
    
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NGPRenderCamera):
            return False
        return self.focal_length == __o.focal_length and np.array_equal(self.transform, __o.transform)
    
    def __ne__(self, __o: object) -> bool:
        if not isinstance(__o, NGPRenderCamera):
            return True
        
        return not self.__eq__(__o)
