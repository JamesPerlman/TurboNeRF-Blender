bl_info = {
    "name": "Export NeRF Render.json",
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
from bpy.props import StringProperty

from blender_nerf_tools.blender_utility.nerf_scene import NeRFScene

def mat_to_list(m: mathutils.Matrix) -> list[float]:
    return [list(r) for r in m]

class BlenderNeRFExportRenderJSON(bpy.types.Operator):

    """Export main camera as NeRF render.json"""
    bl_idname = "blender_nerf_tools.export_render_json"
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
        
        print(f"Exporting camera path to: {output_path}")

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
        global_transform = NeRFScene.global_transform()
        # if global_transform != None:
        #     offset_matrix = global_transform.matrix_world.inverted()

        # Walk through all frames, create a camera dict for each frame
        frames = []
        i = 0
        for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
            scene.frame_set(frame)

            m = offset_matrix @ camera.matrix_world
            o = m.to_quaternion().to_matrix()
            t = m.translation

            aabb_max = NeRFScene.get_aabb_max()
            aabb_min = NeRFScene.get_aabb_min()

            # TODO: abstract this out into a function
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

            # aperture and focus distance
            ngp_aperture = 0
            ngp_focus_target = [0, 0, 0]

            if cam_data.dof.use_dof and cam_data.dof.focus_object != None:
                # No idea if this is correct
                ngp_aperture = cam_data.dof.aperture_fstop
                ngp_focus_target = cam_data.dof.focus_object.matrix_world.translation
            
            # near plane
            ngp_near = cam_data.clip_start

            # create camera dict for this frame
            cam_dict = {
                "file_path": f"{i:05d}.png",
                "aabb" : {
                    "max" : list(aabb_max),
                    "min" : list(aabb_min),
                },
                "camera_angle_x": ngp_ax,
                "transform_matrix": [list(r) for r in m],
                "n_steps": NeRFScene.get_training_steps(),
                "time": NeRFScene.get_time(),
                "aperture": ngp_aperture,
                "focus_target": list(ngp_focus_target),
                "near": ngp_near,
                "far": 1e5,
            }

            frames.append(cam_dict)
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

