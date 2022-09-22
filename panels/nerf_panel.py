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
from blender_nerf_tools.panels.nerf_panel_operators.redraw_point_cloud import BlenderNeRFRedrawPointCloudOperator
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
        bpy.utils.register_class(BlenderNeRFRedrawPointCloudOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(NeRFPanelSettings)
        bpy.utils.unregister_class(BlenderNeRFSetupSceneOperator)
        bpy.utils.unregister_class(ImportColmapOperator)
        bpy.utils.unregister_class(BlenderNeRFRedrawPointCloudOperator)
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
        
        # Setup Scene action
        
        row = setup_section.row()
        row.operator(BlenderNeRFSetupSceneOperator.bl_idname)

        # Import COLMAP action
        
        row = setup_section.row()
        row.operator(ImportColmapOperator.bl_idname)
        row.enabled = is_scene_set_up

        # Redraw Point Cloud action

        row = setup_section.row()
        row.operator(BlenderNeRFRedrawPointCloudOperator.bl_idname)
 
        # row.operator(BlenderNeRFResyncCOLMAPOperator.bl_idname)

        if not is_scene_set_up:
            return

        # AABB section

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


