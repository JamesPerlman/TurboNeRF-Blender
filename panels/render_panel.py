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
    MASK_MODE_ADD,
    MASK_MODE_SUBTRACT,
    MASK_TYPE_BOX,
    MASK_TYPE_CYLINDER,
    MASK_TYPE_SPHERE,
    OBJ_TYPE_ID,
    OBJ_TYPE_RENDER_CAMERA,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
)

from blender_nerf_tools.panels.render_panel_operators.camera_manager_operators import BlenderNeRFAddRenderCameraOperator
from blender_nerf_tools.panels.render_panel_operators.operator_export_nerf_render_json import BlenderNeRFExportRenderJSON
from blender_nerf_tools.panels.render_panel_operators.mask_shape_operators import BlenderNeRFAddMaskShapeOperator

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

MASK_MODES = {
    MASK_MODE_ADD: {
        "name": "Add",
        "description": "Points inside the shape are added to the mask",
    },
    MASK_MODE_SUBTRACT: {
        "name": "Subtract",
        "description": "Points inside the shape are subtracted from the mask",
    },
}

MASK_TYPES = {
    MASK_TYPE_BOX: {
        "name": "Box",
        "description": "Featherable box-shaped mask",
    },
    MASK_TYPE_CYLINDER: {
        "name": "Cylinder",
        "description": "Featherable cylinder-shaped mask",
    },
    MASK_TYPE_SPHERE: {
        "name": "Sphere",
        "description": "Featherable spherical mask",
    },
}

class NeRFRenderPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example

    # Cameras
    camera_model_options = [(tid, CAMERA_TYPES[tid]["name"], CAMERA_TYPES[tid]["description"]) for tid in CAMERA_TYPES]

    camera_model: bpy.props.EnumProperty(
        name="Add",
        items=camera_model_options,
        description="Camera model to use for rendering",
        default=RENDER_CAM_TYPE_PERSPECTIVE,
    )

    # Masks

    mask_mode_options = [(mid, MASK_MODES[mid]["name"], MASK_MODES[mid]["description"]) for mid in MASK_MODES]

    mask_mode: bpy.props.EnumProperty(
        name="Mode",
        items=mask_mode_options,
        description="Mask mode",
        default=MASK_MODE_ADD,
    )

    mask_shape_options = [(tid, MASK_TYPES[tid]["name"], MASK_TYPES[tid]["description"]) for tid in MASK_TYPES]


    mask_shape: bpy.props.EnumProperty(
        name="Add",
        items=mask_shape_options,
        description="Mask shape to use for rendering",
        default=MASK_TYPE_BOX,
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
        bpy.utils.register_class(BlenderNeRFAddMaskShapeOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""

        bpy.utils.unregister_class(NeRFRenderPanelSettings)

        bpy.utils.unregister_class(BlenderNeRFAddRenderCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFExportRenderJSON)
        bpy.utils.unregister_class(BlenderNeRFAddMaskShapeOperator)

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

        row = section.row()
        row.operator(
            BlenderNeRFAddRenderCameraOperator.bl_idname,
            text=f"Create {CAMERA_TYPES[settings.camera_model]['name']} Camera"
        )

        # Masks section

        section = layout.box()
        section.label(
            text="Masks"
        )

        row = section.row()
        row.prop(settings, "mask_shape")

        row = section.row()
        row.prop(settings, "mask_mode")

        row = section.row()
        row.operator(
            BlenderNeRFAddMaskShapeOperator.bl_idname,
            text=f"Create {MASK_TYPES[settings.mask_shape]['name']} Mask"
        )
        
        # Export section

        section = layout.box()
        section.label(text="Export")

        row = section.row()
        row.operator(BlenderNeRFExportRenderJSON.bl_idname, text="Export Render.json")
