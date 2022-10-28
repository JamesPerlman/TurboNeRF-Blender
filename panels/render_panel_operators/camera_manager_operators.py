import bpy

from blender_nerf_tools.constants import (
    RENDER_CAM_IS_ACTIVE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
)
from blender_nerf_tools.panels.render_panel_operators.camera_models.quadrilateral_hexahedron_camera import add_quadrilateral_hexahedron_camera
from blender_nerf_tools.panels.render_panel_operators.camera_models.spherical_quadrilateral_camera import add_spherical_quadrilateral_camera

class BlenderNeRFAddRenderCameraOperator(bpy.types.Operator):
    bl_idname = "blender_nerf_tools.add_render_camera"
    bl_label = "Add Render Camera"
    bl_description = "Add a camera to the scene for rendering"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        settings = context.scene.nerf_render_panel_settings
        camera_model_id = settings.camera_model

        camera = {}
        
        if camera_model_id == RENDER_CAM_TYPE_PERSPECTIVE:
            pass
        elif camera_model_id == RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL:
            camera = add_spherical_quadrilateral_camera()
        elif camera_model_id == RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON:
            camera = add_quadrilateral_hexahedron_camera()
            pass

        # TODO: Camera management            
        camera[RENDER_CAM_IS_ACTIVE_ID] = True

        return {"FINISHED"}