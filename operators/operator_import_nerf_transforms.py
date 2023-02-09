bl_info = {
    "name": "Import Instant-NGP Properties",
    "blender": (3, 0, 0),
    "category": "Import",
}

import bpy
import json
import os
import mathutils
import math
from pathlib import Path

# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

# Thank you https://blender.stackexchange.com/a/126596/141797

class ImportNeRFTransforms(bpy.types.Operator):

    """Import NeRF Transforms"""
    bl_idname = "blender_nerf_tools.import_transforms"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def execute(self, context):
        input_path = Path(self.filepath)
        print(f"Importing instant-ngp properties from: {input_path}")

        # Get some scene references
        scene = bpy.context.scene

        # Open JSON file and interpret
        data: dict
        with open(input_path, 'r') as f:
            data = json.loads(f.read())

        frames = data["frames"]

        # Walk through all cameras in json, and create a blender camera
        for f in frames:
            
            camera_data = bpy.data.cameras.new(name='Camera')
            camera_obj = bpy.data.objects.new('Camera', camera_data)
            scene.collection.objects.link(camera_obj)

            # fetch properties from JSON object
            # rot_mat = mathutils.Matrix(f["orientation"])
            # t_vec = mathutils.Vector(f["translation"])

            # # rotation
            # camera_obj.rotation_mode = 'QUATERNION'
            # camera_obj.rotation_quaternion = rot_mat.to_quaternion()

            # # translation
            # camera_obj.location = t_vec
            camera_obj.matrix_world = mathutils.Matrix(f["transform_matrix"])

            # focal len
            # sensor_diag = math.sqrt(camera_data.sensor_width ** 2 + camera_data.sensor_height ** 2)
            sensor_width = camera_data.sensor_width
            camera_data.lens = 0.5 * sensor_width / math.tan(0.5 * float(data["camera_angle_x"]))
            
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
    self.layout.operator(ImportNeRFTransforms.bl_idname, text="NeRF Transforms (JSON)")

def register():
    bpy.utils.register_class(ImportNeRFTransforms)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportNeRFTransforms)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

#
# Invoke register if started from editor
if __name__ == "__main__":
    register()
