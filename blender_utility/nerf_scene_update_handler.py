import bpy
import numpy as np

from turbo_nerf.blender_utility.obj_type_utility import get_closest_parent_of_type, get_nerf_obj_type
from turbo_nerf.constants import CAMERA_INDEX_ID, NERF_ITEM_IDENTIFIER_ID, OBJ_TYPE_NERF, OBJ_TYPE_TRAIN_CAMERA
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn
from turbo_nerf.utility.render_camera_utils import bl2nerf_cam_train

scene_objects: dict = {}

def filter_nerf_objs(objs: set) -> list:
    return [o for o in objs if get_nerf_obj_type(o) == OBJ_TYPE_NERF]

def get_duplicated_nerf_objs(prev_objs: set, cur_objs: set) -> list:
    added_objs = cur_objs - prev_objs

    if len(added_objs) == 0:
        return []
    
    prev_nerf_objs = filter_nerf_objs(prev_objs)
    added_nerf_objs = filter_nerf_objs(added_objs)
  
    prev_nerf_ids = [o[NERF_ITEM_IDENTIFIER_ID] for o in prev_nerf_objs]
    added_nerf_ids = [o[NERF_ITEM_IDENTIFIER_ID] for o in added_nerf_objs]

    duplicate_nerf_ids = set(prev_nerf_ids).intersection(set(added_nerf_ids))

    return [o for o in added_nerf_objs if o[NERF_ITEM_IDENTIFIER_ID] in duplicate_nerf_ids]

def get_deleted_nerf_ids(prev_objs: set, cur_objs: set) -> list:
    removed_objs = prev_objs - cur_objs
    
    if (len(removed_objs) == 0):
        return []

    all_nerf_ids = [nerf.id for nerf in NeRFManager.get_all_nerfs()]
    cur_nerf_ids = [o[NERF_ITEM_IDENTIFIER_ID] for o in filter_nerf_objs(cur_objs)]

    return [id for id in all_nerf_ids if id not in cur_nerf_ids]

@bpy.app.handlers.persistent
def depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    
    # check if we have new objects
    global scene_objects
    prev_scene_objs = scene_objects.get(scene.name, set())
    cur_scene_objs = set(scene.objects)
    scene_objects[scene.name] = cur_scene_objs

    duplicated_nerf_objs = get_duplicated_nerf_objs(
        prev_objs=prev_scene_objs,
        cur_objs=cur_scene_objs
    )

    # if we have any duplicated objects, we need to create new nerfs for them.
    # each nerf obj must have a unique nerf associated with it.
    for nerf_obj in duplicated_nerf_objs:
        new_nerf_id = NeRFManager.clone(nerf_obj)
        nerf_obj[NERF_ITEM_IDENTIFIER_ID] = new_nerf_id

    # check if we have deleted objects
    deleted_nerf_ids = get_deleted_nerf_ids(
        prev_objs=prev_scene_objs,
        cur_objs=cur_scene_objs
    )

    for nerf_id in deleted_nerf_ids:
        NeRFManager.destroy(nerf_id)
    
    # update object transforms, etc
    for update in depsgraph.updates:
        if update.is_updated_transform:
            obj = update.id
            if not isinstance(obj, bpy.types.Object):
                continue

            nerf_obj_type = get_nerf_obj_type(obj)
            if nerf_obj_type is None:
                continue

            # Only proceed if the object is some child of a NeRF
            nerf_obj = get_closest_parent_of_type(obj, OBJ_TYPE_NERF)
            if nerf_obj is None:
                continue

            # Training Camera
            if nerf_obj_type == OBJ_TYPE_TRAIN_CAMERA:
                cam_obj = obj
                nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
                nerf = NeRFManager.get_nerf_by_id(nerf_id)
                camera_idx = cam_obj[CAMERA_INDEX_ID]
                nerf.dataset.set_camera_at(camera_idx, bl2nerf_cam_train(cam_obj, relative_to=nerf_obj))
                nerf.is_dataset_dirty = True

def register_depsgraph_updates():
    global scene_objects
    scene_objects = {}
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)

def unregister_depsgraph_updates():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)
