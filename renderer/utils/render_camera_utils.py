import bpy
import numpy as np

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
        print(f"{view_matrix}")

    
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NGPRenderCamera):
            return False
        return self.focal_length == __o.focal_length and np.array_equal(self.transform, __o.transform)
    
    def __ne__(self, __o: object) -> bool:
        if not isinstance(__o, NGPRenderCamera):
            return True
        
        return not self.__eq__(__o)
