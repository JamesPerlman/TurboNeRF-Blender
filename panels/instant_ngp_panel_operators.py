import bpy
from instant_ngp_tools.blender_utility.logging_utility import log_report
from instant_ngp_tools.blender_utility.ngp_scene import NGPScene

class InstantNGPSetupSceneOperator(bpy.types.Operator):
    """An Operator to set up everything necessary for controlling the Instant-NGP scene."""

    bl_idname = "instant_ngp_tools.setup_scene"
    bl_label = "Set up Instant-NGP Scene"
    bl_description = "Add scene objects for controlling Instant-NGP renders"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return not NGPScene.is_setup()

    def execute(self, context):
        """Create scene objects."""
        NGPScene.create_main_collection()
        NGPScene.create_aabb_box()
        NGPScene.create_global_transform()
        return {"FINISHED"}
