bl_info = {
    "name": "Import Instant-NGP Properties",
    "blender": (3, 0, 0),
    "category": "Import",
}

import math
import bpy
import json
import mathutils
import numpy as np
from pathlib import Path

# invoke() function w'hich calls the file selector.
from bpy.props import StringProperty, BoolProperty

FLIP_MAT = np.array([
    [1, 0, 0],
    [0, -1, 0],
    [0, 0, -1]
])

# Thank you https://blender.stackexchange.com/a/126596/141797

class ImportHyperNeRFCams(bpy.types.Operator):

    """Import NeRF Transforms"""
    bl_idname = "blender_nerf_tools.import_hypernerf"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})
    directory: StringProperty()
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        input_path = Path(self.directory)
        print(f"Importing HyperNeRF cameras from: {input_path}")

        # Walk through all cameras in json, and create a blender camera
        for i in range(1, 100):
            
            # Open JSON file and interpret
            cam_path = input_path / f"{i:04d}.json"

            if not cam_path.exists():
                continue
            
            data: dict
            with open(cam_path, 'r') as f:
                data = json.loads(f.read())
                
            camera_data = bpy.data.cameras.new(name='Camera')
            camera_obj = bpy.data.objects.new('Camera', camera_data)
            bpy.context.scene.collection.objects.link(camera_obj)

            # fetch properties from JSON object
            o = np.matmul(FLIP_MAT, np.array(data["orientation"])).T
            p = np.array(data["position"])

            m = mathutils.Matrix(np.concatenate((np.concatenate((o, np.array([p]).T), axis=1), [[0, 0, 0, 1]])))
            
            camera_obj.matrix_world = m
            
            # focal len
            fz = float(data["focal_length"])
            h = float(data["image_size"][1])
            camera_data.lens = fz * camera_data.sensor_width / h
            
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
    self.layout.operator(ImportHyperNeRFCams.bl_idname, text="HyperNeRF Cameras")

def register():
    bpy.utils.register_class(ImportHyperNeRFCams)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportHyperNeRFCams)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

#
# Invoke register if started from editor
if __name__ == "__main__":
    register()
