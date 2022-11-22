import json
import math
from pathlib import Path
import bpy
import numpy as np

from bpy.props import StringProperty

from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene
from blender_nerf_tools.constants import (
    CAMERA_CX_ID,
    CAMERA_CY_ID,
    CAMERA_FAR_ID,
    CAMERA_FX_ID,
    CAMERA_FY_ID,
    CAMERA_IMAGE_HEIGHT_ID,
    CAMERA_IMAGE_PATH_ID,
    CAMERA_IMAGE_WIDTH_ID,
    CAMERA_K1_ID,
    CAMERA_K2_ID,
    CAMERA_NEAR_ID,
    CAMERA_P1_ID,
    CAMERA_P2_ID,
)

# utils

# focal length to view angle
def fl_to_angle(fl, dim):
    """Compute the view angle from the focal length."""
    return 2 * math.atan(dim / (2 * fl))

# matrix to serializable list
def mat_to_list(mat):
    return [list(r) for r in mat]

# prop maps

GLOBAL_PROP_MAP = [
    (CAMERA_IMAGE_WIDTH_ID, "w", int),
    (CAMERA_IMAGE_HEIGHT_ID, "h", int),
    (CAMERA_FX_ID, "fl_x", float),
    (CAMERA_FY_ID, "fl_y", float),
    (CAMERA_K1_ID, "k1", float),
    (CAMERA_K2_ID, "k2", float),
    (CAMERA_P1_ID, "p1", float),
    (CAMERA_P2_ID, "p2", float),
    (CAMERA_CX_ID, "cx", float),
    (CAMERA_CY_ID, "cy", float),
]

CAM_PROP_MAP = [
    (CAMERA_NEAR_ID, "near", float),
    (CAMERA_FAR_ID, "far", float),
]


def encode_props(obj, prop_map):
    """Parse the property map."""
    props = {}
    for (nerf_prop_id, dataset_key_id, encoder) in prop_map:
        props[dataset_key_id] = encoder(obj[nerf_prop_id])
    return props

def encode_camera_props(cam):
    """Encode the camera properties."""
    props = {}
    props["near"] = cam[CAMERA_NEAR_ID] * np.max(np.array(cam.matrix_world.to_scale()))
    props["far"] = cam[CAMERA_FAR_ID] 
    return props

# aabb scale (for NGP)
def get_aabb_scale():
    size = max(NeRFScene.get_aabb_size()) * 0.33
    # get the closest power of 2
    return 2 ** math.ceil(math.log2(size))

class BlenderNeRFExportDatasetOperator(bpy.types.Operator):
    """Export the dataset."""
    bl_idname = "blender_nerf.export_dataset"
    bl_label = "Export Dataset"
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    use_relative_paths: bpy.props.BoolProperty(
        name="Use Relative Paths",
        description="Use relative paths for images",
        default=True,
    )

    def execute(self, context):
        """Execute the operator."""
        
        output_path = Path(self.filepath)
        if output_path.suffix != ".json":
            print(f"{output_path} - {output_path.suffix}")
            self.report({"ERROR"}, "Export destination must be a JSON file")
            return {"CANCELLED"}
        
        cams = NeRFScene.get_training_cameras()
        if len(cams) == 0:
            self.report({"ERROR"}, "No NeRF cameras found")
            return {"CANCELLED"}
        
        # get frames
        frames = []
        for cam in cams:
            props = encode_camera_props(cam)
            file_path = Path(cam[CAMERA_IMAGE_PATH_ID])

            if self.use_relative_paths:
                file_path = file_path.relative_to(output_path.parent)
                print(f"{file_path}")
            
            frame = {
                **props,
                "file_path": str(file_path.as_posix()),
                "transform_matrix": mat_to_list(cam.matrix_world),
            }
            frames.append(frame)

        # get global properties
        globals = encode_props(cams[0], GLOBAL_PROP_MAP)
        globals["camera_angle_x"] = fl_to_angle(globals["fl_x"], globals["w"])
        globals["camera_angle_y"] = fl_to_angle(globals["fl_y"], globals["h"])
        globals["aabb_scale"] = get_aabb_scale()

        transforms = {
            **globals,
            "frames": frames,
        }
        
        # write to file
        with open(output_path, "w") as json_file:
            json_file.write(json.dumps(transforms, indent=2))

        return {"FINISHED"}
    

    def invoke(self, context, event):
        self.filepath = "transforms.json"
        # Open browser, take reference to "self" read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {"RUNNING_MODAL"}
