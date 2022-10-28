import numpy as np
import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    FloatVectorProperty,
    FloatProperty,
)
from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene

from blender_nerf_tools.blender_utility.object_utility import (
    get_selected_empty,
    get_selected_object,
)
from blender_nerf_tools.constants import (
    OBJ_TYPE_ID,
    OBJ_TYPE_RENDER_CAMERA,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
)

from blender_nerf_tools.panels.render_panel_operators.camera_manager_operators import BlenderNeRFAddRenderCameraOperator
from blender_nerf_tools.panels.render_panel_operators.operator_export_nerf_render_json import BlenderNeRFExportRenderJSON

CAMERA_TYPES = {
    RENDER_CAM_TYPE_PERSPECTIVE: {
        "name": "Perspective",
        "description": "Standard perspective camera",
    },
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL: {
        "name": "Spherical Quadrilateral",
        "description": "A rectangular quadrilateral that can be curved",
    },
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON: {
        "name": "Quadrilateral Hexahedron",
        "description": "A 6-sided polyhedron that can be used for inverted perspective, ortho, or normal perspective.",
    }
}

class NeRFRenderPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example

    # Cameras
    camera_model_options = [(tid, CAMERA_TYPES[tid]["name"], CAMERA_TYPES[tid]["description"]) for tid in CAMERA_TYPES]

    def update_camera_model(self, context):
        print(CAMERA_TYPES[self.camera_model]["name"])

    camera_model: bpy.props.EnumProperty(
        name="Camera Model",
        items=camera_model_options,
        description="Camera model to use for rendering",
        default=RENDER_CAM_TYPE_PERSPECTIVE,
        update=update_camera_model,
    )


class NeRFRenderPanel(bpy.types.Panel):
    """Class that defines the NeRF render panel in the 3D View"""

    bl_label = "NeRF Render Panel"
    bl_idname = "VIEW3D_PT_blender_NeRF_render_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NeRF Render"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return NeRFScene.is_setup()

    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""

        bpy.utils.register_class(NeRFRenderPanelSettings)
        bpy.types.Scene.nerf_render_panel_settings = PointerProperty(
            type=NeRFRenderPanelSettings
        )

        bpy.utils.register_class(BlenderNeRFAddRenderCameraOperator)
        bpy.utils.register_class(BlenderNeRFExportRenderJSON)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""

        bpy.utils.unregister_class(NeRFRenderPanelSettings)

        bpy.utils.unregister_class(BlenderNeRFAddRenderCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFExportRenderJSON)

        del bpy.types.Scene.nerf_render_panel_settings


    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        settings = context.scene.nerf_render_panel_settings
        layout = self.layout

        # Cameras Section

        section = layout.box()
        section.label(
            text="Cameras"
        )

        row = section.row()
        row.prop(settings, "camera_model")

        row.operator(BlenderNeRFAddRenderCameraOperator.bl_idname, text=f"Create {settings.camera_model}")
        
        # Export section

        section = layout.box()
        section.label(text="Export")

        row = section.row()
        row.operator(BlenderNeRFExportRenderJSON.bl_idname, text="Export Render.json")
