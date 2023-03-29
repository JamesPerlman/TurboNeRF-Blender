import bpy
import json
from pathlib import Path

from turbo_nerf.blender_utility.obj_type_utility import (
    get_all_training_cam_objs,
    get_closest_parent_of_type,
    get_first_child_of_type,
    is_nerf_obj_type,
    is_self_or_some_parent_of_type,
)

from turbo_nerf.constants import (
    CAMERA_FAR_ID,
    CAMERA_NEAR_ID,
    NERF_AABB_SIZE_LOG2_ID,
    NERF_ITEM_IDENTIFIER_ID,
    OBJ_TYPE_NERF,
)
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn
from turbo_nerf.utility.render_camera_utils import bl2nerf_cam

class SynchronizeNeRFDatasetOperator(bpy.types.Operator):
    """An Operator to synchronize a NeRF dataset with the python bridge."""
    bl_idname = "turbo_nerf.synchronize_dataset"
    bl_label = "Synchronize Dataset"
    bl_description = "Synchronize a dataset with the python bridge"

    @classmethod
    def poll(cls, context):
        nerf_obj = get_closest_parent_of_type(context.active_object, OBJ_TYPE_NERF)
        if nerf_obj is None:
            return False
        
        nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
        
        nerf = NeRFManager.items[nerf_id].nerf

        return nerf.is_dataset_dirty

    def execute(self, context):

        nerf_obj = get_closest_parent_of_type(context.active_object, OBJ_TYPE_NERF)
        nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]

        nerf = NeRFManager.items[nerf_id].nerf

        dataset = nerf.dataset.copy()

        dataset.bounding_box = tn.BoundingBox(2 ** nerf_obj[NERF_AABB_SIZE_LOG2_ID])

        cam_objs = get_all_training_cam_objs(nerf_obj)

        nerf_cams = []
        for cam_obj in cam_objs:
            nerf_cam = bl2nerf_cam(cam_obj, img_dims=dataset.image_dimensions)
            nerf_cam.near = cam_obj[CAMERA_NEAR_ID]
            nerf_cam.far = cam_obj[CAMERA_FAR_ID]
            nerf_cams.append(nerf_cam)
        
        dataset.cameras = nerf_cams

        nerf.update_dataset(dataset)

        return {'FINISHED'}
