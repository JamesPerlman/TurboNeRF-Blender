__reload_order_index__ = -1

from blender_nerf_tools.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_IMG_PLANE,
    OBJ_TYPE_TRAIN_CAMERA,
)

def get_object_type(obj):
    if OBJ_TYPE_ID in obj:
        return obj[OBJ_TYPE_ID]
    else:
        return None

def is_training_camera(obj):
    return get_object_type(obj) == OBJ_TYPE_TRAIN_CAMERA

def is_image_plane(obj):
    return get_object_type(obj) == OBJ_TYPE_IMG_PLANE
