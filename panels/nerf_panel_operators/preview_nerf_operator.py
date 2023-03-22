import bpy

class PreviewNeRFOperator(bpy.types.Operator):
    bl_idname = "view3d.show_nerf_preview"
    bl_label = "Show NeRF Preview"
    
    @classmethod
    def poll(cls, context):
        shading_type_is_rendered = context.space_data.shading.type == 'RENDERED'
        render_engine_is_turbo_nerf = context.scene.render.engine == 'TURBO_NERF_RENDERER'
        return not (shading_type_is_rendered and render_engine_is_turbo_nerf)
    
    def execute(self, context):
        context.space_data.shading.type = 'RENDERED'
        context.scene.render.engine = 'TURBO_NERF_RENDERER'
        return {'FINISHED'}
