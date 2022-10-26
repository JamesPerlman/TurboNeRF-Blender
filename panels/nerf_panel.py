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
from blender_nerf_tools.constants import OBJ_TYPE_ID, OBJ_TYPE_IMG_PLANE
from blender_nerf_tools.operators.operator_export_nerf_dataset import BlenderNeRFExportDatasetOperator
from blender_nerf_tools.panels.nerf_panel_operators.redraw_point_cloud import BlenderNeRFRedrawPointCloudOperator
from blender_nerf_tools.panels.nerf_panel_operators.scene_operators import BlenderNeRFAutoAlignSceneOperator, BlenderNeRFFitSceneInBoundingBoxOperator
from blender_nerf_tools.panels.nerf_panel_operators.setup_scene import BlenderNeRFSetupSceneOperator
from blender_nerf_tools.panels.nerf_panel_operators.camera_selection_operators import (
    BlenderNeRFSelectAllCamerasOperator,
    BlenderNeRFSelectCamerasInsideRadiusOperator,
    BlenderNeRFSelectCamerasOutsideRadiusOperator,
    BlenderNeRFSelectFirstCameraOperator,
    BlenderNeRFSelectLastCameraOperator,
    BlenderNeRFSelectNextCameraOperator,
    BlenderNeRFSelectPreviousCameraOperator,
    BlenderNeRFSetActiveFromSelectedCameraOperator,
    BlenderNeRFUpdateCameraImagePlaneVisibilityOperator,
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
    def get_selected_cameras(self):
        return NeRFScene.get_selected_cameras()
    
    def set_selected_camera(self, id):
        NeRFScene.set_selected_camera(id)
    
    camera_selection_radius: FloatProperty(
        name="Camera Selection Radius",
        description="Radius for camera selection",
        default=1.0,
        min=0.0,
        max=100.0,
    )

    def get_distance_to_cursor(self, camera):
        return (bpy.context.scene.cursor.location - camera.location).length

    # Camera properties

    def get_camera_near(self):
        return NeRFScene.get_near_for_selected_cameras()
    
    def set_camera_near(self, value):
        NeRFScene.set_near_for_selected_cameras(value)
    
    camera_near: FloatProperty(
        name="Camera Near",
        description="Camera near plane",
        get=get_camera_near,
        set=set_camera_near,
        min=0.0,
        max=100.0,
    )

    def get_camera_far(self):
        return NeRFScene.get_far_for_selected_cameras()

    def set_camera_far(self, value):
        NeRFScene.set_far_for_selected_cameras(value)
    
    camera_far: FloatProperty(
        name="Camera Far",
        description="Camera far plane",
        get=get_camera_far,
        set=set_camera_far,
        min=0.0,
        max=1000000,
    )


    def get_use_selected_cameras_for_training(self):
        return NeRFScene.get_use_selected_cameras_for_training()
    
    def set_use_selected_cameras_for_training(self, value):
        NeRFScene.set_use_selected_cameras_for_training(
            value,
            show_non_training_cameras=self.show_non_training_cameras
        )

    use_for_training: BoolProperty(
        name="Use for Training",
        description="Use selected camera(s) for training",
        get=get_use_selected_cameras_for_training,
        set=set_use_selected_cameras_for_training,
    )

    def update_show_non_training_cameras(self, context):
        NeRFScene.update_cameras_visibility(
            show_non_training_cameras=self.show_non_training_cameras
        )
    
    show_non_training_cameras: BoolProperty(
        name="Show Non-Training Cameras",
        description="Show non-training cameras",
        update=update_show_non_training_cameras,
        default=True,
    )

    # Image planes

    def get_should_force_image_plane_visibility(self):
        if self.show_image_planes == False:
            return False
        elif self.show_image_planes_for_active_cameras_only == True:
            return None
        else:
            return True

    def update_show_image_planes(self, context):
        force_visible = self.get_should_force_image_plane_visibility()
        NeRFScene.update_image_plane_visibility_for_all_cameras(force_visible)

    show_image_planes: BoolProperty(
        name="Show Image Planes",
        description="Show image planes for cameras",
        default=True,
        update=update_show_image_planes,
    )
    
    show_image_planes_for_active_cameras_only: BoolProperty(
        name="Show Image Planes for Active Cameras Only",
        description="Show image planes for active cameras only",
        default=True,
        update=update_show_image_planes,
    )

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
        bpy.utils.register_class(BlenderNeRFSelectCamerasInsideRadiusOperator)
        bpy.utils.register_class(BlenderNeRFSelectCamerasOutsideRadiusOperator)
        bpy.utils.register_class(BlenderNeRFSelectFirstCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectLastCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectNextCameraOperator)
        bpy.utils.register_class(BlenderNeRFSelectPreviousCameraOperator)
        bpy.utils.register_class(BlenderNeRFSetActiveFromSelectedCameraOperator)
        bpy.utils.register_class(BlenderNeRFUpdateCameraImagePlaneVisibilityOperator)
        bpy.utils.register_class(BlenderNeRFExportDatasetOperator)
        bpy.utils.register_class(BlenderNeRFAutoAlignSceneOperator)
        bpy.utils.register_class(BlenderNeRFFitSceneInBoundingBoxOperator)

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
        bpy.utils.unregister_class(BlenderNeRFSelectCamerasInsideRadiusOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectCamerasOutsideRadiusOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectFirstCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectLastCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectNextCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSelectPreviousCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFSetActiveFromSelectedCameraOperator)
        bpy.utils.unregister_class(BlenderNeRFUpdateCameraImagePlaneVisibilityOperator)
        bpy.utils.unregister_class(BlenderNeRFExportDatasetOperator)
        bpy.utils.unregister_class(BlenderNeRFAutoAlignSceneOperator)
        bpy.utils.unregister_class(BlenderNeRFFitSceneInBoundingBoxOperator)

        del bpy.types.Scene.nerf_panel_settings
        
    @classmethod
    def subscribe_to_events(cls):
        """Subscribe to events."""

        def obj_selected_callback():
            active_obj = bpy.context.view_layer.objects.active
            if active_obj[OBJ_TYPE_ID] == OBJ_TYPE_IMG_PLANE:
                NeRFScene.set_selected_camera(active_obj.parent, change_view=False)
            NeRFScene.update_image_plane_visibility_for_all_cameras(
                force_visible=bpy.context.scene.nerf_panel_settings.get_should_force_image_plane_visibility()
            )
        
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

    def draw(self, context):
        """Draw the panel with corresponding properties and operators."""

        settings = context.scene.nerf_panel_settings
        layout = self.layout
        is_scene_set_up = NeRFScene.is_setup()

        section = layout.box()
        section.label(
            text="Scene"
        )
        
        # Setup Scene action
        
        row = section.row()
        row.operator(BlenderNeRFSetupSceneOperator.bl_idname)

        if not is_scene_set_up:
            return
        
        # Import COLMAP action
        
        row = section.row()
        row.operator(ImportColmapOperator.bl_idname)
        row.enabled = is_scene_set_up

        # Redraw Point Cloud action

        point_cloud_exists = NeRFScene.point_cloud() is not None

        point_section = layout.box()
        point_section.label(
            text="Point Cloud"
        )

        row = point_section.row()
        row.prop(settings, "viz_point_size")
        row.enabled = point_cloud_exists

        row = point_section.row()
        row.operator(BlenderNeRFRedrawPointCloudOperator.bl_idname)
        row.enabled = point_cloud_exists
        
        # Camera Settings section

        section = layout.box()
        section.label(
            text="Camera selection"
        )

        # Select previous/next camera

        row = section.row()
        selected_cams = settings.get_selected_cameras()

        if len(selected_cams) == 0:
            row.label(text="No cameras selected")
        
        if len(selected_cams) == 1:
            row.label(text=f"Current: {selected_cams[0].name}")
        elif len(selected_cams) > 1:
            row.label(text=f"{len(selected_cams)} cameras selected")

        row = section.row()
        row.operator(BlenderNeRFSetActiveFromSelectedCameraOperator.bl_idname, text="Set Active")
        row.enabled = len(selected_cams) == 1
        
        # camera stepper row
        row = section.row()
        row.operator(BlenderNeRFSelectFirstCameraOperator.bl_idname, text="|<")
        row.operator(BlenderNeRFSelectPreviousCameraOperator.bl_idname, text="<")
        row.operator(BlenderNeRFSelectNextCameraOperator.bl_idname, text=">")
        row.operator(BlenderNeRFSelectLastCameraOperator.bl_idname, text=">|")

        # Select all cameras
        row = section.row()
        row.operator(BlenderNeRFSelectAllCamerasOperator.bl_idname)

        # Select cameras in radius
        if len(selected_cams) == 1:
            row = section.row()
            row.label(text=f"Dist to cursor: {settings.get_distance_to_cursor(selected_cams[0]):.2f}")

        row = section.row()
        row.label(text="Select by radius:")

        row = section.row()
        row.prop(
            settings,
            "camera_selection_radius",
            text="radius",
        )

        row = section.row()
        row.operator(BlenderNeRFSelectCamerasInsideRadiusOperator.bl_idname, text="In")
        row.operator(BlenderNeRFSelectCamerasOutsideRadiusOperator.bl_idname, text="Out")
        
        # Properties for selected cameras
        section = layout.box()
        section.label(text="Camera Properties")

        row = section.row()
        row.prop(
            settings,
            "camera_near",
            text="near",
        )

        row = section.row()
        row.prop(
            settings,
            "camera_far",
            text="far",
        )

        row = section.row()
        row.prop(
            settings,
            "use_for_training",
            text="Use For Training",
        )

        row = section.row()
        row.prop(
            settings,
            "show_non_training_cameras",
            text="Show Non-Training Cameras",
        )

        # Camera image plane visibility
        section = layout.box()
        section.label(text="Image Planes")

        row = section.row()
        row.prop(
            settings,
            "show_image_planes",
            text="Show image planes",
        )

        row = section.row()
        row.prop(
            settings,
            "show_image_planes_for_active_cameras_only",
            text="Selected cameras only",
        )
        row.enabled = settings.show_image_planes

        row = section.row()
        row.operator(BlenderNeRFUpdateCameraImagePlaneVisibilityOperator.bl_idname, text="Update Image Planes")

        # AABB section

        section = layout.box()
        section.label(
            text="Axis-Aligned Bounding Box"
        )

        row = section.row()
        row.prop(
            settings,
            "aabb_max",
            text="Max"
        )
        row.enabled = is_scene_set_up

        row = section.row()
        row.prop(
            settings,
            "aabb_min",
            text="Min",
        )
        row.enabled = is_scene_set_up

        row = section.row()
        row.prop(
            settings,
            "aabb_size",
            text="Size",
        )
        row.enabled = is_scene_set_up

        row = section.row()
        row.prop(
            settings,
            "aabb_center",
            text="Center"
        )
        row.enabled = is_scene_set_up

        row = section.row()
        row.prop(
            settings,
            "is_aabb_cubical",
            text="Cube"
        )
        row.enabled = is_scene_set_up

        # Scene section
        section = layout.box()
        section.label(text="Scene")

        row = section.row()
        row.operator(BlenderNeRFAutoAlignSceneOperator.bl_idname, text="Auto Align Scene")
        row.operator(BlenderNeRFFitSceneInBoundingBoxOperator.bl_idname, text="Fit Scene in AABB")
        

        # Export section

        section = layout.box()
        section.label(text="Export")

        row = section.row()
        row.operator(BlenderNeRFExportDatasetOperator.bl_idname, text="Export Dataset")
