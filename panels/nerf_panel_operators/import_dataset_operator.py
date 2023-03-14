import bpy
import json
import math
import mathutils
from pathlib import Path

from turbo_nerf.blender_utility.object_utility import add_cube
from turbo_nerf.constants import (
    NERF_AABB_SIZE_ID,
    NERF_AABB_CENTER_ID,
    NERF_DATASET_PATH_ID,
)
from turbo_nerf.utility.nerf_manager import NeRFManager

class ImportNeRFDatasetOperator(bpy.types.Operator):
    """An Operator to import a NeRF dataset from a directory."""
    bl_idname = "turbo_nerf.import_dataset"
    bl_label = "Import Dataset"
    bl_description = "Import a dataset from a directory"

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return NeRFManager.can_import()

    def execute(self, context):
        # Get some scene references
        scene = context.scene

        print(f"Importing NeRF dataset from: {self.filepath}")

        nerf_id = NeRFManager.create_trainable(dataset_path=self.filepath)
        tn_nerf = NeRFManager.items[nerf_id].nerf
        bbox = tn_nerf.get_bounding_box()

        bl_nerf = add_cube("NeRF", size=bbox.get_size(), collection=scene.collection)
        bl_nerf.display_type = "WIRE"
        context.view_layer.objects.active = bl_nerf
        bpy.ops.object.modifier_add(type='WIREFRAME')

        bl_nerf[NERF_AABB_SIZE_ID] = bbox.get_size()
        bl_nerf[NERF_AABB_CENTER_ID] = [0, 0, 0]

        bl_nerf[NERF_DATASET_PATH_ID] = self.filepath
        
        # Open JSON file and interpret
        data: dict
        with open(Path(self.filepath), 'r') as f:
            data = json.loads(f.read())

        frames = data["frames"]

        # Walk through all cameras in json, and create a blender camera
        for f in frames:
            
            camera_data = bpy.data.cameras.new(name='Camera')
            camera_obj = bpy.data.objects.new('Camera', camera_data)
            scene.collection.objects.link(camera_obj)
            camera_obj.parent = bl_nerf

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
            

        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}

def menu_func_import(self, context):
    self.layout.operator(ImportNeRFDatasetOperator.bl_idname, text="NeRF Dataset")

def register():
    bpy.utils.register_class(ImportNeRFDatasetOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportNeRFDatasetOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
