import bpy
from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.blender_utility.object_utility import delete_object
from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from turbo_nerf.utility.nerf_manager import NeRFManager


class UnloadNeRFTrainingDataOperator(bpy.types.Operator):
    bl_idname = "nerf.remove_dataset"
    bl_label = "Remove NeRF Dataset"
    bl_description = "Remove the currently imported NeRF dataset"
    
    @classmethod
    def poll(cls, context):
        has_active_nerf = get_active_nerf_obj(context) is not None
        is_training = NeRFManager.is_training()
        return has_active_nerf and not is_training

    def execute(self, context):
        nerf_obj = get_active_nerf_obj(context)
        nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]

        delete_object(nerf_obj)

        if NeRFManager.is_image_data_loaded():
            NeRFManager.unload_training_images()
        
        NeRFManager.destroy(nerf_id)

        context.scene.nerf_dataset_panel_props.imported_dataset_path = ""

        return {'FINISHED'}
