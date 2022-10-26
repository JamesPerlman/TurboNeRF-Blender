__reload_order_index__ = -1

import bpy
from blender_nerf_tools.blender_utility.logging_utility import log_report
from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene

class BlenderNeRFSetupSceneOperator(bpy.types.Operator):
    """An Operator to set up everything necessary for controlling the NeRF scene."""

    bl_idname = "blender_nerf_tools.setup_scene"
    bl_label = "Set up NeRF Scene"
    bl_description = "Add scene objects for controlling NeRF scenes"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return not NeRFScene.is_setup()

    def execute(self, context):
        """Create scene objects."""

        NeRFScene.setup()

        return {"FINISHED"}
