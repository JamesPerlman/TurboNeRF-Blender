import bpy

from turbo_nerf.utility.nerf_manager import NeRFManager

class TrainNeRFOperator(bpy.types.Operator):
    """Class that defines the operator for training NeRF."""

    bl_idname = "turbo_nerf.train_nerf"
    bl_label = "Train NeRF"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return NeRFManager.can_train()

    def execute(self, context):
        """Execute the operator."""

        NeRFManager.toggle_training()

        return {"FINISHED"}
