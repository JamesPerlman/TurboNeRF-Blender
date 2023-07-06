import bpy

from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from turbo_nerf.utility.nerf_manager import NeRFManager

class ResetNeRFTrainingOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.reset_nerf_training"
    bl_label = "Reset NeRF Training"

    @classmethod
    def poll(cls, context):
        nerf_obj = get_active_nerf_obj(context)
        nerf = NeRFManager.get_nerf_for_obj(nerf_obj)
        
        return nerf.training_step > 0
    
    def execute(self, context):
        nerf_obj = get_active_nerf_obj(context)
        NeRFManager.reset_training(nerf_obj)
        return {'FINISHED'}
