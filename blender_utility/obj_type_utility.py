__reload_order_index__ = -1

from turbo_nerf.constants import (
    OBJ_TYPE_CAMERAS_CONTAINER,
    OBJ_TYPE_ID,
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
    cams = []
    for cam_obj in cams_container.children:
        if is_nerf_obj_type(cam_obj, OBJ_TYPE_TRAIN_CAMERA):
            cams.append(cam_obj)
    return cams