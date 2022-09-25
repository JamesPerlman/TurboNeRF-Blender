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

class BlenderNeRFSelectCamerasInRadiusOperator(bpy.types.Operator):
    """Select cameras in radius"""
    bl_idname = "blender_nerf_tools.select_cameras_in_radius"
    bl_label = "Select Cameras in Radius"
    bl_description = "Select cameras in radius"

    def execute(self, context):
        NeRFScene.deselect_all_cameras()
        settings = context.scene.nerf_settings
        radius = settings.cam_select_radius
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                if obj.location.length <= radius:
                    obj.select_set(True)
        return {'FINISHED'}