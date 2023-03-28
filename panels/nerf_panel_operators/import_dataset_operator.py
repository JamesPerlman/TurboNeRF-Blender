import bpy
import json
import math
import mathutils
from pathlib import Path

import numpy as np
from turbo_nerf.blender_utility.driver_utility import force_update_drivers, lock_prop_with_driver
from turbo_nerf.blender_utility.obj_type_utility import set_nerf_obj_type

from turbo_nerf.blender_utility.object_utility import add_cube, add_empty
from turbo_nerf.constants import (
    NERF_AABB_CENTER_ID,
    NERF_AABB_SIZE_LOG2_ID,
    NERF_DATASET_PATH_ID,
    OBJ_TYPE_NERF,
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
        nerf = NeRFManager.items[nerf_id].nerf
        dataset = nerf.dataset
        bbox = nerf.get_bounding_box()

        cams = dataset.cameras
        
        bl_nerf = add_cube("NeRF", size=1.0, collection=scene.collection)
        bl_nerf.display_type = "WIRE"

        set_nerf_obj_type(bl_nerf, OBJ_TYPE_NERF)

        bl_nerf[NERF_AABB_SIZE_LOG2_ID] = int(round(math.log2(bbox.get_size())))
        aabb_size_log2 = bl_nerf.id_properties_ui(NERF_AABB_SIZE_LOG2_ID)
        aabb_size_log2.update(min=0, max=7)

        # add AABB
        aabb = add_cube("AABB", size=1.0, collection=scene.collection)
        aabb.display_type = "WIRE"
        aabb.parent = bl_nerf

        context.view_layer.objects.active = aabb
        bpy.ops.object.modifier_add(type='WIREFRAME')

        # drivers for linking scale to aabb_size_log2
        [sx, sy, sz] = [fc.driver for fc in aabb.driver_add('scale')]
        for driver in [sx, sy, sz]:
            var_x = driver.variables.new()
            var_x.name = 'aabb_size_log2'
            var_x.targets[0].id = bl_nerf
            var_x.targets[0].data_path = f'["{NERF_AABB_SIZE_LOG2_ID}"]'
            driver.expression = '2**aabb_size_log2'
        
        # lock location to [0,0,0]
        lock_prop_with_driver(aabb, 'location', 0.0)

        # lock rotation to [0,0,0]
        lock_prop_with_driver(aabb, 'rotation_euler', 0.0)

        # lock rotation_mode to XYZ
        lock_prop_with_driver(aabb, 'rotation_mode', 1)

        # Add empty for Cameras
        cams_empty = add_empty("CAMERAS", collection=scene.collection)
        cams_empty.parent = bl_nerf
        
        # Walk through all cameras in json, and create a blender camera
        for cam in cams:
            cam_data = bpy.data.cameras.new(name='Camera')
            cam_obj = bpy.data.objects.new('Camera', cam_data)
            scene.collection.objects.link(cam_obj)
            cam_obj.parent = cams_empty

            # set transform
            cam_obj.matrix_world = mathutils.Matrix(np.array(cam.transform.to_nerf().to_matrix()))
            
            # set focal length
            fl_x, fl_y = cam.focal_length
            cam_w, cam_h = cam.resolution
            sensor_width = cam_data.sensor_width
            cam_data.lens = sensor_width / cam_w * fl_x

        context.view_layer.objects.active = bl_nerf
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
