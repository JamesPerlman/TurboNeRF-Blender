import bpy

from blender_nerf_tools.blender_utility.obj_type_utility import get_nerf_obj_type
from blender_nerf_tools.constants import (
    OBJ_TYPE_MASK_SHAPE,
    OBJ_TYPE_RENDER_CAMERA,
    RENDER_CAM_IS_ACTIVE_ID,
)

class NeRFRenderManager:
    @classmethod
    def get_all_cameras(cls):
        return [obj for obj in bpy.data.objects if cls.is_render_camera(obj)]
    
    @classmethod
    def is_render_camera(cls, obj):
        return get_nerf_obj_type(obj) == OBJ_TYPE_RENDER_CAMERA
    
    @classmethod
    def get_active_camera(cls):
        render_cameras = [cam for cam in cls.get_all_cameras() if bool(cam[RENDER_CAM_IS_ACTIVE_ID]) is True]
        return render_cameras[0] if len(render_cameras) > 0 else None

    @classmethod
    def is_mask(cls, obj):
        return get_nerf_obj_type(obj) == OBJ_TYPE_MASK_SHAPE
    
    @classmethod
    def get_all_masks(cls):
        return [obj for obj in bpy.data.objects if cls.is_mask(obj)]
