import numpy as np
import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    FloatVectorProperty,
)
from instant_ngp_tools.blender_utility.ngp_scene import NGPScene

from instant_ngp_tools.blender_utility.object_utility import (
    get_selected_empty,
    get_selected_object,
)
from instant_ngp_tools.panels.instant_ngp_panel_operators import InstantNGPSetupSceneOperator

class InstantNGPPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the InstantNGP panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example
    def get_aabb_min(self):
        return NGPScene.get_aabb_min()

    def set_aabb_min(self, value):
        NGPScene.set_aabb_min(value)

    aabb_min: FloatVectorProperty(
        name="AABB Min",
        description="Crops scene for locations less than this value.",
        get=get_aabb_min,
        set=set_aabb_min,
        size=3,
        precision=5,
        min=-100,
        max=100,
    )

    def get_aabb_max(self):
        return NGPScene.get_aabb_max()

    def set_aabb_max(self, value):
        NGPScene.set_aabb_max(value)
    
    aabb_max: FloatVectorProperty(
        name="AABB Max",
        description="Crops scene for locations greater than this value.",
        get=get_aabb_max,
        set=set_aabb_max,
        size=3,
        precision=5,
        min=-100,
        max=100,
    )

    def get_use_ngp_coords(self):
        return True
    
    def set_use_ngp_coords(self, value):
        pass
    
    use_ngp_coords: BoolProperty(
        name="Use NGP Coords",
        description="Use default NGP to NeRF scale (0.33) and offset (0.5, 0.5, 0.5).",
        get=get_use_ngp_coords,
        set=set_use_ngp_coords,
    )


class InstantNGPPanel(bpy.types.Panel):
    """Class that defines the Instant-NGP panel in the 3D view."""

    bl_label = "Instant-NGP Panel"
    bl_idname = "VIEW3D_PT_instant_ngp_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "InstantNGP_NeRF"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True

    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""

        bpy.utils.register_class(InstantNGPPanelSettings)
        bpy.types.Scene.instant_ngp_panel_settings = PointerProperty(
            type=InstantNGPPanelSettings
        )
        bpy.utils.register_class(InstantNGPSetupSceneOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(InstantNGPPanelSettings)
        bpy.utils.unregister_class(InstantNGPSetupSceneOperator)
        del bpy.types.Scene.instant_ngp_panel_settings

    def draw(self, context):
        """Draw the panel with corrresponding properties and operators."""
        settings = context.scene.instant_ngp_panel_settings
        layout = self.layout

        aabb_box = NGPScene.aabb_box()
        glob_trans = NGPScene.global_transform()

        is_scene_set_up = NGPScene.is_setup()

        setup_section = layout.box()
        setup_section.label(
            text="Instant-NGP Scene is set up." if is_scene_set_up else "Set up Instant-NGP Scene Objects."
        )
        row = setup_section.row()
        row.operator(InstantNGPSetupSceneOperator.bl_idname)

        aabb_section = layout.box()
        aabb_section.label(
            text="AABB Cropping"
        )

        row = aabb_section.row()
        row.prop(
            settings,
            "aabb_max",
            text="Max"
        )
        row.enabled = is_scene_set_up

        row = aabb_section.row()
        row.prop(
            settings,
            "aabb_min",
            text="Min",
        )
        row.enabled = is_scene_set_up

        row = aabb_section.row()
        row.prop(
            settings,
            "use_ngp_coords",
            text="Use NGP Coords"
        )

        export_screenshot_box = layout.box()
        export_screenshot_box.label(
            text="Export a single or multiple"
            " screenshots (of the 3D view) to disk."
        )
        row = export_screenshot_box.row()
        row.prop(settings, "screenshot_file_format", text="File Format")
        row = export_screenshot_box.row()
        row.prop(settings, "only_3d_view", text="Export Only 3D view")
        row = export_screenshot_box.row()
        row.prop(
            settings,
            "use_camera_perspective",
            text="Use Perspective of selected Camera",
        )
        row.enabled = selected_cam is not None
        row = export_screenshot_box.row()
        row.operator(ExportScreenshotImageOperator.bl_idname)
        row = export_screenshot_box.row()
        row.prop(
            settings,
            "use_camera_keyframes_for_screenshots",
            text="Use Camera Keyframes",
        )
        row.enabled = (
            selected_cam is not None
            and selected_cam.animation_data is not None
        )
        row = export_screenshot_box.row()
        row.operator(ExportScreenshotAnimationOperator.bl_idname)

        write_point_cloud_box = layout.box()
        write_point_cloud_box.label(
            text="Select a camera to save or export an OpenGL point cloud"
            " rendering"
        )
        row = write_point_cloud_box.row()
        row.prop(
            settings,
            "save_point_size",
            text="Point Size of OpenGL Point Cloud",
        )
        row.enabled = selected_cam is not None
        save_point_cloud_box = write_point_cloud_box.box()
        save_point_cloud_box.label(text="Save point cloud rendering:")
        row = save_point_cloud_box.row()
        row.operator(SaveOpenGLRenderImageOperator.bl_idname)

        export_point_cloud_box = write_point_cloud_box.box()
        export_point_cloud_box.label(text="Export point cloud rendering:")
        row = export_point_cloud_box.row()
        row.prop(settings, "render_file_format", text="File Format")
        row.enabled = selected_cam is not None
        row = export_point_cloud_box.row()
        row.prop(settings, "save_alpha", text="Save Alpha Values")
        row.enabled = selected_cam is not None
        row = export_point_cloud_box.row()
        row.operator(ExportOpenGLRenderImageOperator.bl_idname)
        row = export_point_cloud_box.row()
        row.prop(
            settings,
            "use_camera_keyframes_for_rendering",
            text="Use Camera Keyframes",
        )
        row.enabled = (
            selected_cam is not None
            and selected_cam.animation_data is not None
        )
        row = export_point_cloud_box.row()
        row.operator(ExportOpenGLRenderAnimationOperator.bl_idname)
