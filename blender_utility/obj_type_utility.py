__reload_order_index__ = -1

from turbo_nerf.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_IMG_PLANE,
    OBJ_TYPE_TRAIN_CAMERA,
)

def get_nerf_obj_type(obj):
    if OBJ_TYPE_ID in obj:
        return obj[OBJ_TYPE_ID]
    else:
        return None
