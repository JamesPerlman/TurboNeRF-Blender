import bpy

from turbo_nerf.constants.raymarching import RAYMARCHING_MAX_STEP_SIZE, RAYMARCHING_MIN_STEP_SIZE
from turbo_nerf.utility.nerf_manager import NeRFManager

class TurboNeRFRenderEngineRaymarchingSettings(bpy.types.PropertyGroup):
    """Settings for the Turbo NeRF render engine."""

    preview_min_step_size: bpy.props.FloatProperty(
        name="Preview Min Step Size",
        description="Minimum step size for preview renders",
        min=RAYMARCHING_MIN_STEP_SIZE,
        max=RAYMARCHING_MAX_STEP_SIZE,
        get=NeRFManager.bridge_obj_prop_getter("previewer", "min_step_size", default=RAYMARCHING_MIN_STEP_SIZE),
        set=NeRFManager.bridge_obj_prop_setter("previewer", "min_step_size"),
        precision=6,
    )

    render_min_step_size: bpy.props.FloatProperty(
        name="Render Min Step Size",
        description="Minimum step size for final renders",
        min=RAYMARCHING_MIN_STEP_SIZE,
        max=RAYMARCHING_MAX_STEP_SIZE,
        get=NeRFManager.bridge_obj_prop_getter("renderer", "min_step_size", default=RAYMARCHING_MIN_STEP_SIZE),
        set=NeRFManager.bridge_obj_prop_setter("renderer", "min_step_size"),
        precision=6,
    )

class TurboNeRFRenderEngineRaymarchingPanel(bpy.types.Panel):
    """Panel for Turbo NeRF render engine settings."""

    bl_label = "Turbo NeRF"
    bl_idname = "TURBO_NERF_PT_render_engine_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        print(context.scene.render.engine)
        print('render engine?')
        return context.scene.render.engine == "TURBO_NERF_RENDERER"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        ui_props = scene.tn_render_engine_raymarching_settings

        layout.prop(ui_props, "preview_min_step_size")
        layout.prop(ui_props, "render_min_step_size")
    
    @classmethod
    def register(cls):
        print("registeriterig")
        bpy.utils.register_class(TurboNeRFRenderEngineRaymarchingSettings)
        bpy.types.Scene.tn_render_engine_raymarching_settings = bpy.props.PointerProperty(type=TurboNeRFRenderEngineRaymarchingSettings)
    
    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(TurboNeRFRenderEngineRaymarchingSettings)
        del bpy.types.Scene.tn_render_engine_raymarching_settings
