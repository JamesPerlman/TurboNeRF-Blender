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
    
    print(f"Added objects: {len(added_objs)}")
    
    prev_nerfs = filter_nerf_objs(prev_objs)
    added_nerfs = filter_nerf_objs(added_objs)

    print(f"Prev nerfs: {len(prev_nerfs)}")
    print(f"Added nerfs: {len(added_nerfs)}")
    
    # there is probably a more efficient or pythonic way to do this, but this works for now.
    prev_nerf_ids = [o[NERF_ITEM_IDENTIFIER_ID] for o in prev_nerfs]
    added_nerf_ids = [o[NERF_ITEM_IDENTIFIER_ID] for o in added_nerfs]

    duplicate_nerf_ids = set(prev_nerf_ids).intersection(set(added_nerf_ids))
    print(f"Duplicate nerf ids: {len(duplicate_nerf_ids)}")

    return [o for o in added_nerfs if o[NERF_ITEM_IDENTIFIER_ID] in duplicate_nerf_ids]


@bpy.app.handlers.persistent
def depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    # check if we have new objects
    global scene_objects

    cur_scene_objs = set(scene.objects)
    duplicated_nerf_objs = get_duplicated_nerf_objs(
        prev_objs=scene_objects.get(scene.name, set()),
        cur_objs=cur_scene_objs
    )

    print(f"Scene: {scene.name} - {len(duplicated_nerf_objs)} duplicated objects")

    # if we have any duplicated objects, we need to create new nerfs for them.
    # each nerf obj must have a unique nerf associated with it.
    for obj in duplicated_nerf_objs:
        nerf_id = obj[NERF_ITEM_IDENTIFIER_ID]
        nerf = NeRFManager.items[nerf_id].nerf
        new_nerf_id = NeRFManager.clone(nerf)
        obj[NERF_ITEM_IDENTIFIER_ID] = new_nerf_id
    
    # update object transforms, etc
    for update in depsgraph.updates:
        if update.is_updated_transform:
            obj = update.id
            if not isinstance(obj, bpy.types.Object):
                continue

            nerf_obj_type = get_nerf_obj_type(obj)
            if nerf_obj_type is None:
                continue

            # Base NeRF object
            if nerf_obj_type == OBJ_TYPE_NERF:
                nerf_id = obj[NERF_ITEM_IDENTIFIER_ID]
                nerf = NeRFManager.items[nerf_id].nerf
                # something is wrong here
                mat = np.array(obj.matrix_world)
                nerf.transform = tn.Transform4f(mat).from_nerf()
                continue

            # From here on, we check if the object is some child of a NeRF
            nerf_obj = get_closest_parent_of_type(obj, OBJ_TYPE_NERF)
            if nerf_obj is None:
                continue

            # Training Camera
            if nerf_obj_type == OBJ_TYPE_TRAIN_CAMERA:
                cam_obj = obj
                nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
                nerf = NeRFManager.items[nerf_id].nerf
                camera_idx = cam_obj[CAMERA_INDEX_ID]
                nerf.dataset.set_camera_at(camera_idx, bl2nerf_cam_train(cam_obj))
                nerf.is_dataset_dirty = True
    
    scene_objects[scene.name] = cur_scene_objs

def register_depsgraph_updates():
    global scene_objects
    scene_objects = {}
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)

def unregister_depsgraph_updates():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)
