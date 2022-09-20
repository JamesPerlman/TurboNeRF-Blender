bl_info = {
    "name": "Export Instant-NGP Transforms",
    "blender": (3, 0, 0),
    "category": "Export",
}

import bpy
import json
import math
import mathutils
from pathlib import Path

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import StringProperty, BoolProperty, EnumProperty

from instant_ngp_tools.blender_utility.ngp_scene import NGPScene

def mat_to_list(m: mathutils.Matrix) -> list[float]:
    return [list(r) for r in m]

class ExportInstantNGPTransforms(bpy.types.Operator):

    """Export main camera as instant-ngp camera path"""
    bl_idname = "instant_ngp_tools.export_transforms"
    bl_label = "Export"
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
        
        print(f"Exporting instant-ngp camera path to: {output_path}")

        # Get some scene references
        scene = bpy.context.scene
        camera = scene.camera
        cam_data = camera.data
        
        render_scale = scene.render.resolution_percentage / 100.0
        ngp_w = scene.render.resolution_x * render_scale
        ngp_h = scene.render.resolution_y * render_scale

        # TODO: maybe add an eyedropper for this in the blender UI somehow
        # aka don't hardcode the name of this ref object
        offset_matrix = mathutils.Matrix.Identity(4)
        global_transform = NGPScene.global_transform()
        if global_transform != None:
            offset_matrix = global_transform.matrix_world.inverted()

        # Walk through all frames, create an instant-ngp camera for each frame
        ngp_frames = []
        i = 0
        for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
            scene.frame_set(frame)

            m = offset_matrix @ camera.matrix_world
            o = m.to_quaternion().to_matrix()
            t = m.translation

            aabb_max = NGPScene.get_aabb_max()
            aabb_min = NGPScene.get_aabb_min()

            # calculate focal len
            bl_sw = cam_data.sensor_width
            bl_sh = cam_data.sensor_height
            bl_f  = cam_data.lens

            # get blender sensor size in pixels
            px_w: float
            
            if cam_data.sensor_fit == 'AUTO':
                bl_asp = 1.0
                ngp_asp = ngp_h / ngp_w

                if ngp_asp > bl_asp:
                    px_w = ngp_h / bl_asp
                else:
                    px_w = ngp_w

            elif cam_data.sensor_fit == 'HORIZONTAL':
                px_w = ngp_w

            elif cam_data.sensor_fit == 'VERTICAL':
                px_w = ngp_h * bl_sw / bl_sh
            
            
            # focal length in pixels
            px_f = bl_f / bl_sw * px_w

            # ngp fov angles
            ngp_ax = 2.0 * math.atan2(0.5 * ngp_w, px_f)

            # create camera dict for this frame
            cam_dict = {
                "file_path": f"{i:05d}.png",
                "aabb" : {
                    "max" : [aabb_max[0], aabb_max[1], aabb_max[2]],
                    "min" : [aabb_min[0], aabb_min[1], aabb_min[2]],
                },
                "camera_angle_x": ngp_ax,
                "transform_matrix": [
                    [m[0][0], m[0][1], m[0][2], m[0][3]],
                    [m[1][0], m[1][1], m[1][2], m[1][3]],
                    [m[2][0], m[2][1], m[2][2], m[2][3]],
                    [m[3][0], m[3][1], m[3][2], m[3][3]],
                ],
                "n_steps": NGPScene.get_training_steps(),
                "time": NGPScene.get_time(),
            }

            ngp_frames.append(cam_dict)
            i = i + 1
        
        # Write camera path
        blender_fps = scene.frame_step * scene.render.fps / scene.render.fps_base
        ngp_time = (scene.frame_end - scene.frame_start) / blender_fps
        render_scale = scene.render.resolution_percentage / 100.0
        ngp_w = scene.render.resolution_x * render_scale
        ngp_h = scene.render.resolution_y * render_scale

        # calculate focal len
        bl_sw = cam_data.sensor_width
        bl_sh = cam_data.sensor_height
        bl_ax = cam_data.angle_x
        bl_ay = cam_data.angle_y
        bl_f  = cam_data.lens

        # get blender sensor size in pixels
        px_w: float
        px_h: float
        
        if cam_data.sensor_fit == 'AUTO':
            bl_asp = 1.0
            ngp_asp = ngp_h / ngp_w

            if ngp_asp > bl_asp:
                px_w = ngp_h / bl_asp
                px_h = ngp_h
            else:
                px_w = ngp_w
                px_h = ngp_w * bl_asp

        elif cam_data.sensor_fit == 'HORIZONTAL':
            px_w = ngp_w
            px_h = ngp_w * bl_sh / bl_sw

        elif cam_data.sensor_fit == 'VERTICAL':
            px_w = ngp_h * bl_sw / bl_sh
            px_h = ngp_h
        
        
        # focal length in pixels
        px_f = bl_f / bl_sw * px_w

        # ngp fov angles
        ngp_ax = 2.0 * math.atan2(0.5 * ngp_w, px_f)
        ngp_ay = 2.0 * math.atan2(0.5 * ngp_h, px_f)

        ngp_transforms = {
            "camera_angle_x": ngp_ax,
            "camera_angle_y": ngp_ay,
            "fl_x": px_f,
            "fl_y": px_f,
            "k1": 0.0,
            "k2": 0.0,
            "p1": 0.0,
            "p2": 0.0,
            "cx": 0.5 * ngp_w,
            "cy": 0.5 * ngp_h,
            "w": ngp_w,
            "h": ngp_h,
            "frames": ngp_frames,
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

