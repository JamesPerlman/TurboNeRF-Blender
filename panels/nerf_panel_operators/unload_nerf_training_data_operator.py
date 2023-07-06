import bpy
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.blender_utility.object_utility import delete_object
from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from turbo_nerf.utility.nerf_manager import NeRFManager


class UnloadNeRFTrainingDataOperator(bpy.types.Operator):
    bl_idname = "nerf.unload_training_data"
    bl_label = "Unload Training Data"
    bl_description = "Clear the training data from the currently-selected NeRF object."
    
    @classmethod
    def poll(cls, context):
        nerf_obj = get_active_nerf_obj(context)
        return NeRFManager.is_image_data_loaded(nerf_obj)

    def execute(self, context):
        nerf_obj = get_active_nerf_obj(context)

        if NeRFManager.is_image_data_loaded(nerf_obj):
            NeRFManager.unload_training_images(nerf_obj)

        return {'FINISHED'}
