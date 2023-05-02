bl_info = {
    "name": "Export NeRF Render.json",
    "blender": (3, 0, 0),
    "category": "Export",
}

import bpy
import json
import numpy as np
from pathlib import Path

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import StringProperty

from turbo_nerf.utility.render_camera_utils import bl2nerf_cam

class ExportRenderCamJSON(bpy.types.Operator):

    """Export main camera as NeRF render.json"""
    bl_idname = "turbo_nerf.export_render_cam_json"
    bl_label = "Export TurboNeRF Render JSON"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filename_ext = ".json"
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def execute(self, context):
        output_path = Path(self.filepath)
        if output_path.suffix != '.json':
            print(f"{output_path} - {output_path.suffix}")
            self.report({'ERROR'}, 'Export destination must be a JSON file')
            return {'CANCELLED'}
        
        print(f"Exporting camera path to: {output_path}")

        # Get some scene references
        scene = bpy.context.scene
        
        render_scale = scene.render.resolution_percentage / 100.0
        render_w = int(scene.render.resolution_x * render_scale)
        render_h = int(scene.render.resolution_y * render_scale)
        render_dims = (render_w, render_h)

        # Walk through all frames, create a camera dict for each frame
        frames = []
        i = 0
        for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
            scene.frame_set(frame)

            active_cam = bpy.context.scene.camera
            
            nerf_cam = bl2nerf_cam(active_cam, render_dims)

            focal_len, _ = nerf_cam.focal_length
            
            # create dict for this frame
            frame_dict = {
                "camera": {
                    "transform": np.array(nerf_cam.transform.to_matrix()).tolist(),
                    "near": nerf_cam.near,
                    "far": nerf_cam.far,
                    "focal_length": focal_len,
                }
            }

            frames.append(frame_dict)
            i = i + 1



        ngp_transforms = {
            "w": render_w,
            "h": render_h,
            "frames": frames,
        }

        with open(output_path, 'w') as json_file:
            json_file.write(json.dumps(ngp_transforms, indent=2))
        
        # Clean up
        scene.frame_set(scene.frame_start)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "render.json"
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}

