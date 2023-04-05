import bpy

from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from turbo_nerf.utility.nerf_manager import NeRFManager

class ResetNeRFTrainingOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.reset_nerf_training"
    bl_label = "Reset NeRF Training"
    
    def execute(self, context):
        NeRFManager.reset_training()
        return {'FINISHED'}
