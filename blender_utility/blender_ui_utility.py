import bpy

def switch_to_turbo_nerf_renderer(context: bpy.types.Context):
    if is_turbo_nerf_renderer_active(context):
        return
    
    context.space_data.shading.type = 'RENDERED'
    context.scene.render.engine = 'TURBO_NERF_RENDERER'
    context.scene.display_settings.display_device = 'None'


def is_turbo_nerf_renderer_active(context: bpy.types.Context):
    shading_type_is_rendered = context.space_data.shading.type == 'RENDERED'
    render_engine_is_turbo_nerf = context.scene.render.engine == 'TURBO_NERF_RENDERER'
    is_display_device_none = context.scene.display_settings.display_device == 'None'

    return shading_type_is_rendered and render_engine_is_turbo_nerf and is_display_device_none