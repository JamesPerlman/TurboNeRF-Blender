__reload_order_index__ = -1

import bpy

from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene

class BlenderNeRFSelectAllCamerasOperator(bpy.types.Operator):
    """Select all cameras in the scene."""
    bl_idname = "blender_nerf.select_all_cameras"
    bl_label = "Select All Cameras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Execute the operator."""
        NeRFScene().select_all_cameras()
        return {"FINISHED"}

class BlenderNeRFSelectFirstCameraOperator(bpy.types.Operator):
    """Select the first camera."""
    bl_idname = "blender_nerf.select_first_camera"
    bl_label = "Select First Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        NeRFScene.select_first_camera()
        return {'FINISHED'}

class BlenderNeRFSelectLastCameraOperator(bpy.types.Operator):
    """Select the last camera."""
    bl_idname = "blender_nerf.select_last_camera"
    bl_label = "Select Last Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        NeRFScene.select_last_camera()
        return {'FINISHED'}

class BlenderNeRFSelectPreviousCameraOperator(bpy.types.Operator):
    """Select the previous camera."""
    bl_idname = "blender_nerf.select_previous_camera"
    bl_label = "Select Previous Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return len(NeRFScene.get_selected_cameras()) == 1

    def execute(self, context):
        NeRFScene.select_previous_camera()
        return {'FINISHED'}

class BlenderNeRFSelectNextCameraOperator(bpy.types.Operator):
    """Select the next camera."""
    bl_idname = "blender_nerf.select_next_camera"
    bl_label = "Select Next Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return len(NeRFScene.get_selected_cameras()) == 1

    def execute(self, context):
        NeRFScene.select_next_camera()
        return {'FINISHED'}

class BlenderNeRFSelectCamerasInsideRadiusOperator(bpy.types.Operator):
    """Select cameras in radius"""
    bl_idname = "blender_nerf_tools.select_cameras_in_radius"
    bl_label = "Select Cameras in Radius"
    bl_description = "Select cameras in radius"

    def execute(self, context):
        NeRFScene.select_cameras_inside_radius(bpy.context.scene.nerf_panel_settings.camera_selection_radius)
        return {'FINISHED'}

class BlenderNeRFSelectCamerasOutsideRadiusOperator(bpy.types.Operator):
    """Select cameras outside radius"""
    bl_idname = "blender_nerf_tools.select_cameras_outside_radius"
    bl_label = "Select Cameras Outside Radius"
    bl_description = "Select cameras outside radius"

    def execute(self, context):
        NeRFScene.select_cameras_outside_radius(bpy.context.scene.nerf_panel_settings.camera_selection_radius)
        return {'FINISHED'}

class BlenderNeRFSetActiveFromSelectedCameraOperator(bpy.types.Operator):
    """Set active camera from selected camera"""
    bl_idname = "blender_nerf_tools.set_active_from_selected_camera"
    bl_label = "Set Active Camera from Selected Camera"
    bl_description = "Set active camera from selected camera"

    def execute(self, context):
        NeRFScene.set_selected_camera(NeRFScene.get_selected_cameras()[0])
        return {'FINISHED'}

class BlenderNeRFUpdateCameraImagePlaneVisibilityOperator(bpy.types.Operator):
    """Update camera image plane visibility"""
    bl_idname = "blender_nerf_tools.update_camera_image_plane_visibility"
    bl_label = "Update Camera Image Plane Visibility"
    bl_description = "Update camera image plane visibility"

    def execute(self, context):
        NeRFScene.update_image_plane_visibility_for_all_cameras(
            force_visible=context.scene.nerf_panel_settings.get_should_force_image_plane_visibility()
        )
        return {'FINISHED'}
