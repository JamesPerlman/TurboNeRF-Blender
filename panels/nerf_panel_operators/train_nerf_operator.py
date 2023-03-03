import bpy

from blender_nerf_tools.utility.nerf_manager import NeRFManager

class TrainNeRFOperator(bpy.types.Operator):
    """Class that defines the operator for training NeRF."""

    bl_idname = "blender_nerf_tools.train_nerf"
    bl_label = "Train NeRF"
    bl_options = {"REGISTER"}

    def execute(self, context):
        """Execute the operator."""

        NeRFManager.toggle_training()

        return {"FINISHED"}
