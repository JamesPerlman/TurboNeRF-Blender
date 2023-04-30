import bpy
import json
from pathlib import Path

from turbo_nerf.blender_utility.obj_type_utility import (
    get_active_nerf_obj,
    get_all_training_cam_objs,
    get_nerf_for_obj,
    is_self_or_some_parent_of_type,
)

from turbo_nerf.constants import (
    NERF_AABB_SIZE_LOG2_ID,
    OBJ_TYPE_NERF,
)
from turbo_nerf.utility.nerf_manager import NeRFManager
from turbo_nerf.utility.pylib import PyTurboNeRF as tn
from turbo_nerf.utility.render_camera_utils import bl2nerf_cam_train

class ExportNeRFDatasetOperator(bpy.types.Operator):
    """An Operator to export a NeRF dataset from a directory."""
    bl_idname = "turbo_nerf.export_dataset"
    bl_label = "Export Dataset"
    bl_description = "Export a dataset from a directory"

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return is_self_or_some_parent_of_type(context.active_object, OBJ_TYPE_NERF)

    def execute(self, context):
        # Get some scene references
        nerf_obj = get_active_nerf_obj(context)
        nerf = get_nerf_for_obj(nerf_obj)

        dataset = nerf.dataset.copy()
        dataset.file_path = Path(self.filepath)

        dataset.bounding_box = tn.BoundingBox(2 ** nerf_obj[NERF_AABB_SIZE_LOG2_ID])

        cam_objs = get_all_training_cam_objs(nerf_obj)

        nerf_cams = []
        for cam_obj in cam_objs:
            nerf_cam = bl2nerf_cam_train(cam_obj)
            nerf_cams.append(nerf_cam)
    
        dataset.cameras = nerf_cams

        json_data: dict = dataset.to_json()

        with open(self.filepath, 'w') as f:
            f.write(json.dumps(json_data, indent=4))

        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "transforms.json"
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}
