__reload_order_index__ = -1

import bpy
from turbo_nerf.constants import (
    OBJ_TYPE_CAMERAS_CONTAINER,
    OBJ_TYPE_ID,
    OBJ_TYPE_NERF,
    OBJ_TYPE_TRAIN_CAMERA,
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

def get_closest_parent_of_type(obj, obj_type):
    target = obj
    while target is not None:
        if is_nerf_obj_type(target, obj_type):
            return target
        target = target.parent
    return None

def is_self_or_some_parent_of_type(obj, obj_type):
    return get_closest_parent_of_type(obj, obj_type) is not None

def get_first_child_of_type(obj, obj_type):
    for child in obj.children:
        if is_nerf_obj_type(child, obj_type):
            return child

    for child in obj.children:
        target = get_first_child_of_type(child, obj_type)
        if target is not None:
            return target

    return None

def get_all_training_cam_objs(nerf_obj):
    cams_container = get_first_child_of_type(nerf_obj, OBJ_TYPE_CAMERAS_CONTAINER)
    
    if cams_container is None:
        return []
    
    return [c for c in cams_container.children if is_nerf_obj_type(c, OBJ_TYPE_TRAIN_CAMERA)]

def get_active_nerf_obj(context):
    active_obj = context.active_object
    nerf_obj = get_closest_parent_of_type(active_obj, OBJ_TYPE_NERF)
    return nerf_obj

def get_nerf_training_cams(nerf_obj, context):
    cam_objs = [o for o in context.selected_objects if is_nerf_obj_type(o, OBJ_TYPE_TRAIN_CAMERA)]

    if len(cam_objs) == 0:
        cam_objs = get_all_training_cam_objs(nerf_obj)
    
    if len(cam_objs) == 0:
        return []
    
    return cam_objs
