__reload_order_index__ = -1

import bpy

from blender_nerf_tools.photogrammetry_importer.opengl.utility import redraw_points

class BlenderNeRFRedrawPointCloudOperator(bpy.types.Operator):
    """An Operator to redraw point clouds."""

    bl_idname = "blender_nerf_tools.redraw_point_cloud"
    bl_label = "Redraw Point Cloud"
    bl_description = "Redraw point clouds (useful if they are hidden)"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return "contains_opengl_point_clouds_nerf" in bpy.context.scene

    def execute(self, context):
        """Create scene objects."""

        redraw_points(None)

        return {"FINISHED"}
