import bpy

from turbo_nerf.blender_utility.object_utility import add_obj, select_object
from turbo_nerf.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_RENDER_CAMERA,
    RENDER_CAM_IS_ACTIVE_ID,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
)

def add_perspective_camera(name="Perspective Camera", collection=None):
    camera = bpy.data.cameras.new(name)
    camera_obj = add_obj(camera, name, collection)
    
    camera_obj[OBJ_TYPE_ID] = OBJ_TYPE_RENDER_CAMERA
    camera_obj[RENDER_CAM_TYPE_ID] = RENDER_CAM_TYPE_PERSPECTIVE
    camera_obj[RENDER_CAM_IS_ACTIVE_ID] = True

    select_object(camera_obj)
    return camera_obj
