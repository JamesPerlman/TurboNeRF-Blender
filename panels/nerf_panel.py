import numpy as np
import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    FloatVectorProperty,
)
from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene

from blender_nerf_tools.blender_utility.object_utility import (
    get_selected_empty,
    get_selected_object,
)
from blender_nerf_tools.panels.nerf_panel_operators.setup_scene import BlenderNeRFSetupSceneOperator
from blender_nerf_tools.photogrammetry_importer.operators.colmap_import_op import ImportColmapOperator

class NeRFPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example
    # AABB Min
    def get_aabb_min(self):
        return NeRFScene.get_aabb_min()

    def set_aabb_min(self, value):
        NeRFScene.set_aabb_min(value)

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

    # AABB Max
    def get_aabb_max(self):
        return NeRFScene.get_aabb_max()

    def set_aabb_max(self, value):
        NeRFScene.set_aabb_max(value)
    
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

    # AABB Size
    def get_aabb_size(self):
        return NeRFScene().get_aabb_size()
    
    def set_aabb_size(self, value):
        NeRFScene().set_aabb_size(value)
    
    aabb_size: FloatVectorProperty(
        name="AABB Size",
        description="Size of AABB box",
        get=get_aabb_size,
        set=set_aabb_size,
    )

    # AABB Center
    def get_aabb_center(self):
        return NeRFScene.get_aabb_center()
    
    def set_aabb_center(self, value):
        NeRFScene.set_aabb_center(value)
    
    aabb_center: FloatVectorProperty(
        name="AABB Center",
        description="Center of AABB box",
        get=get_aabb_center,
        set=set_aabb_center,
    )

    # "Is AABB a Cube"
    def get_is_aabb_cubical(self):
        return NeRFScene.get_is_aabb_cubical()
    
    def set_is_aabb_cubical(self, value):
        NeRFScene.set_is_aabb_cubical(value)

    is_aabb_cubical: BoolProperty(
        name="Use NGP Coords",
        description="Use default NGP to NeRF scale (0.33) and offset (0.5, 0.5, 0.5).",
        get=get_is_aabb_cubical,
        set=set_is_aabb_cubical,
    )


class NeRFPanel(bpy.types.Panel):
    """Class that defines the Instant-NGP panel in the 3D view."""

    bl_label = "NeRF Panel"
    bl_idname = "VIEW3D_PT_blender_nerf_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blender_NeRF"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True

    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""

        bpy.utils.register_class(NeRFPanelSettings)
        bpy.types.Scene.nerf_panel_settings = PointerProperty(
            type=NeRFPanelSettings
        )
        bpy.utils.register_class(BlenderNeRFSetupSceneOperator)
        bpy.utils.register_class(ImportColmapOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(NeRFPanelSettings)
        bpy.utils.unregister_class(BlenderNeRFSetupSceneOperator)
        bpy.utils.unregister_class(ImportColmapOperator)
        del bpy.types.Scene.nerf_panel_settings

    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        settings = context.scene.nerf_panel_settings
        layout = self.layout
        is_scene_set_up = NeRFScene.is_setup()

        setup_section = layout.box()
        setup_section.label(
            text="Scene"
        )
        
        row = setup_section.row()
        row.operator(BlenderNeRFSetupSceneOperator.bl_idname)

        row = setup_section.row()
        row.operator(ImportColmapOperator.bl_idname)
        # row.operator(BlenderNeRFResyncCOLMAPOperator.bl_idname)

        if not is_scene_set_up:
            return

        """AABB"""
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
            "aabb_size",
            text="Size",
        )
        row.enabled = is_scene_set_up

        row = aabb_section.row()
        row.prop(
            settings,
            "aabb_center",
            text="Center"
        )
        row.enabled = is_scene_set_up

        row = aabb_section.row()
        row.prop(
            settings,
            "is_aabb_cubical",
            text="Cube"
        )
        row.enabled = is_scene_set_up

        return
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
