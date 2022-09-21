bl_info = {
    "name": "Import Instant-NGP Properties",
    "blender": (3, 0, 0),
    "category": "Import",
}

import bpy
import json
import mathutils
import math
from pathlib import Path

# invoke() function which calls the file selector.
from bpy.props import StringProperty

NGP_CENTER = mathutils.Vector((0.5, 0.5, 0.5))
NGP_SCALE = 0.33

TO_NGP_TRANSFORM = mathutils.Matrix.Scale(NGP_SCALE, 4) @ mathutils.Matrix.Translation(NGP_CENTER)
FROM_NGP_TRANSFORM = TO_NGP_TRANSFORM.inverted()

# Thank you https://blender.stackexchange.com/a/126596/141797

class ImportInstantNGPCameras(bpy.types.Operator):

    """Import Instant-NGP Properties"""
    bl_idname = "instant-ngp.import_properties"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob = StringProperty(default='*.json', options={'HIDDEN'})

    def execute(self, context):
        input_path = Path(self.filepath)
        print(f"Importing instant-ngp properties from: {input_path}")

        # Open JSON file and interpret
        with open(input_path, 'r') as f:
            data = json.loads(f.read())

        # Walk through all cameras in json, and create a blender camera
        for ngp_cam in ngp_cams:

            # fetch properties from JSON object
            ngp_R = ngp_cam["R"]
            ngp_T = ngp_cam["T"]
            ngp_dof = ngp_cam["dof"]
            ngp_fov = ngp_cam["fov"]
            ngp_scale = ngp_cam["scale"]
            ngp_slice = ngp_cam["slice"]

            # rotation
            camera.rotation_quaternion = mathutils.Quaternion((ngp_R[0], ngp_R[1], ngp_R[2], ngp_R[3]))
            camera.keyframe_insert(data_path="rotation_quaternion", frame=frame)

            # translation
            camera.location = mathutils.Vector((ngp_T[0], ngp_T[1], ngp_T[2]))
            camera.keyframe_insert(data_path="location", frame=frame)

            # focal len
            sensor_diag = math.sqrt(math.pow(cam_data.sensor_width, 2) + math.pow(cam_data.sensor_height, 2))
            cam_data.lens = 0.5 * sensor_diag / math.tan(0.5 * ngp_fov)
            cam_data.keyframe_insert(data_path="lens", frame=frame)
            
            # TODO: depth of field

        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}

def menu_func_import(self, context):
    self.layout.operator(ImportInstantNGPCameras.bl_idname, text="Instant-NGP Cameras")

def register():
    bpy.utils.register_class(ImportInstantNGPCameras)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportInstantNGPCameras)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

#
# Invoke register if started from editor
if __name__ == "__main__":
    register()
