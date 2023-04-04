import bpy

from turbo_nerf.blender_utility.blender_ui_utility import is_turbo_nerf_renderer_active, switch_to_turbo_nerf_renderer

class PreviewNeRFOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.show_nerf_preview"
    bl_label = "Show NeRF Preview"
    
    @classmethod
    def poll(cls, context):
        return not is_turbo_nerf_renderer_active(context)
    
    def execute(self, context):
        switch_to_turbo_nerf_renderer(context)
        return {'FINISHED'}
