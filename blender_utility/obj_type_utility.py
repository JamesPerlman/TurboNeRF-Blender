__reload_order_index__ = -1

from turbo_nerf.constants import (
    OBJ_TYPE_ID,
)

def get_nerf_obj_type(obj):
    if OBJ_TYPE_ID in obj:
        return obj[OBJ_TYPE_ID]
    else:
        return None

def set_nerf_obj_type(obj, obj_type):
    obj[OBJ_TYPE_ID] = obj_type

def is_nerf_obj_type(obj, obj_type):
    return get_nerf_obj_type(obj) == obj_type
