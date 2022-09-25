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
from blender_nerf_tools.panels.nerf_panel_operators.redraw_point_cloud import BlenderNeRFRedrawPointCloudOperator
from blender_nerf_tools.panels.nerf_panel_operators.setup_scene import BlenderNeRFSetupSceneOperator
from blender_nerf_tools.panels.nerf_panel_operators.camera_selection_operators import (
    BlenderNeRFSelectAllCamerasOperator,
    BlenderNeRFSelectCamerasInRadiusOperator,
    BlenderNeRFSelectFirstCameraOperator,
    BlenderNeRFSelectLastCameraOperator,
    BlenderNeRFSelectNextCameraOperator,
    BlenderNeRFSelectPreviousCameraOperator,
)
from blender_nerf_tools.photogrammetry_importer.operators.colmap_import_op import ImportColmapOperator


class NeRFPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the NeRF panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example

    # Point cloud
    def get_viz_point_size(self):
        return NeRFScene.get_viz_point_size()

    def set_viz_point_size(self, value):
        NeRFScene.set_viz_point_size(value)

    viz_point_size: IntProperty(
        name="Point Size",
        description="Point cloud visualization point size.",
        get=get_viz_point_size,
        set=set_viz_point_size,
        min=1,
    )

    # Cameras
    def set_selected_camera(self, id):
        NeRFScene.set_selected_camera(id)
    
    def get_selected_cameras(self):
        return NeRFScene.get_selected_cameras()
    
    camera_selection_radius: FloatProperty(
        name="Camera Selection Radius",
        description="Radius for camera selection",
        default=1.0,
        min=0.0,
        max=100.0,
    )

    def get_distance_to_cursor(self, camera):
        return (bpy.context.scene.cursor.location - camera.location).length

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
        bpy.utils.register_class(BlenderNeRFSelectAllCamerasOperator)
        bpy.utils.register_class(BlenderNeRFSelectCamerasInRadiusOperator)
        bpy.utils.register_class(BlenderNeRFSelectFirstCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectLastCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectNextCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectPreviousCameraOperator)

        cls.subscribe_to_events()



    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""

        cls.unsubscribe_from_events()

        bpy.utils.unregister_class(NeRFPanelSettings)
        bpy.utils.unregister_class(BlenderNeRFSetupSceneOperator)
        bpy.utils.unregister_class(ImportColmapOperator)
        bpy.utils.unregister_class(BlenderNeRFRedrawPointCloudOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectAllCamerasOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectCamerasInRadiusOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectFirstCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectLastCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectNextCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectPreviousCameraOperator)

        del bpy.types.Scene.nerf_panel_settings
        
    @classmethod
    def subscribe_to_events(cls):
        """Subscribe to events."""

        def obj_selected_callback():
            cls.handle_object_selected()
        
        bpy.msgbus.subscribe_rna(
            key = (bpy.types.LayerObjects, "active"),
            owner = cls,
            args = (),
            notify = obj_selected_callback,
        )
    
    @classmethod
    def unsubscribe_from_events(cls):
        """Unsubscribe from events."""

        bpy.msgbus.clear_by_owner(cls)

    @classmethod
    def handle_object_selected(cls):
        NeRFScene.update_visibility_for_selected_cameras()

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

        if not is_scene_set_up:
            return
        
        # Import COLMAP action
        
        row = setup_section.row()
        row.operator(ImportColmapOperator.bl_idname)
        row.enabled = is_scene_set_up

        # Redraw Point Cloud action

        point_cloud_exists = NeRFScene.point_cloud() is not None

        point_cloud_section = layout.box()
        point_cloud_section.label(
            text="Point Cloud"
        )

        row = point_cloud_section.row()
        row.prop(settings, "viz_point_size")
        row.enabled = point_cloud_exists

        row = point_cloud_section.row()
        row.operator(BlenderNeRFRedrawPointCloudOperator.bl_idname)
        row.enabled = point_cloud_exists
        
        # Camera Settings section

        cam_section = layout.box()
        cam_section.label(
            text="Cameras"
        )

        # Select previous/next camera

        row = cam_section.row()
        selected_cams = settings.get_selected_cameras()

        if len(selected_cams) == 0:
            row.label(text="No cameras selected")
        
        if len(selected_cams) == 1:
            row.label(text=f"Current: {selected_cams[0].name}")
        elif len(selected_cams) > 1:
            row.label(text=f"{len(selected_cams)} cameras selected")
        
        row = cam_section.row()

        row.operator(BlenderNeRFSelectFirstCameraOperator.bl_idname, text="|<")
        row.operator(BlenderNeRFSelectPreviousCameraOperator.bl_idname, text="<")
        row.operator(BlenderNeRFSelectNextCameraOperator.bl_idname, text=">")
        row.operator(BlenderNeRFSelectLastCameraOperator.bl_idname, text=">|")

        # Select all cameras
        row = cam_section.row()
        row.operator(BlenderNeRFSelectAllCamerasOperator.bl_idname)

        # Select cameras in radius

        if len(selected_cams) == 1:
            row = cam_section.row()
            row.label(text=f"Dist to cursor: {settings.get_distance_to_cursor(selected_cams[0]):.2f}")

        row = cam_section.row()
        row.label(text="Select in radius:")

        row = cam_section.row()
        row.prop(
            settings,
            "camera_selection_radius",
            text="Cam Select Radius",
        )
        row.operator(BlenderNeRFSelectCamerasInRadiusOperator.bl_idname, text="Select")

        # Set near/far planes
        row = cam_section.row()


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


