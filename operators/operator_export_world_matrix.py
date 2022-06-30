bl_info = {
    "name": "Export Object's World Matrix",
    "blender": (3, 0, 0),
    "category": "Export",
}

import bpy
import copy
import json
import os
import math
import mathutils
from pathlib import Path

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ExportObjectWorldMatrix(bpy.types.Operator):

    """Export selected object's world_matrix"""
    bl_idname = "instant_ngp_tools.export_object_world_matrix"
    bl_label = "Export"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def execute(self, context):
        output_path = Path(self.filepath)
        if output_path.suffix != '.json':
            self.report({'ERROR'}, 'Export destination must be a JSON file')
            return {'CANCELLED'}
        
        selected_objects = bpy.context.selected_objects

        print(f"{selected_objects}")

        if len(selected_objects) != 1:
            self.report({'ERROR'}, 'Please select a single object whose world_transform you wish to export')
            return {'CANCELLED'}
        
        obj = selected_objects[0]

        if obj.matrix_world == None:
            self.report({'ERROR'}, 'Selected object does not have a matrix_world.')
            return {'CANCELLED'}

        print(f"Exporting world_matrix of {obj.name} to: {output_path}")

        m = obj.matrix_world

        obj_dict = {
            "transform_matrix": [
                [m[0][0], m[0][1], m[0][2], m[0][3]],
                [m[1][0], m[1][1], m[1][2], m[1][3]],
                [m[2][0], m[2][1], m[2][2], m[2][3]],
                [m[3][0], m[3][1], m[3][2], m[3][3]],
            ]
        }

        with open(output_path, 'w') as json_file:
            json_file.write(json.dumps(obj_dict, indent=2))

        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "matrix.json"
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}
