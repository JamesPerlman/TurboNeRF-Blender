bl_info = {
    "name": "Export Nerfies Cameras",
    "blender": (3, 0, 0),
    "category": "Export",
}

import bpy
import json
import mathutils
from pathlib import Path

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import StringProperty

FLIP_MAT = mathutils.Matrix([
    [1, 0, 0],
    [0, -1, 0],
    [0, 0, -1],
])

# Thank you https://blender.stackexchange.com/a/126596/141797

class ExportNerfiesCameras(bpy.types.Operator):

    """Export main camera as nerfies camera set"""
    bl_idname = "turbo_nerf.export_nerfies_cameras"
    bl_label = "Export"
    bl_options = {'REGISTER'}

    directory: StringProperty()
    # filter_folder = bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        output_dir = Path(self.directory)
        print(f"Exporting nerfies cameras to: {output_dir}")

        # Get some scene references
        scene = bpy.context.scene
        camera = scene.camera
        cam_data = bpy.data.cameras[camera.name]

        original_cam_rot_mode = camera.rotation_mode
        camera.rotation_mode = 'QUATERNION'

        OUTPUT_WIDTH, OUTPUT_HEIGHT = (1080, 1350)

        # Walk through all frames, export camera.json for each frame
        
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            
            m = camera.matrix_world
            rot = FLIP_MAT @ m.to_quaternion().to_matrix()
            loc = m.to_translation()
            
            cam_dict = {
                "orientation": [list(r) for r in rot],
                "position": list(loc),
                "focal_length": cam_data.lens / cam_data.sensor_width * OUTPUT_WIDTH,
                "principal_point": [OUTPUT_WIDTH / 2, OUTPUT_HEIGHT / 2],
                "skew": 0.0,
                "pixel_aspect_ratio": 1.0,
                "radial_distortion": [0.0, 0.0, 0.0],
                "tangential_distortion": [0.0, 0.0],
                "image_size": [OUTPUT_WIDTH, OUTPUT_HEIGHT],
            }
            
            camera_json_file_path = output_dir / f"{frame:04d}.json"

            with open(camera_json_file_path, 'w') as json_file:
                json_file.write(json.dumps(cam_dict, indent=2))
            
        # Clean up
        camera.rotation_mode = original_cam_rot_mode
        scene.frame_set(scene.frame_start)

        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}

def menu_func_export(self, context):
    self.layout.operator(ExportNerfiesCameras.bl_idname, text="Nerfies Cameras")

def register():
    bpy.utils.register_class(ExportNerfiesCameras)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportNerfiesCameras)

#
# Invoke register if started from editor
if __name__ == "__main__":
    register()
