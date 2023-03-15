bl_info = {
    "name": "Export NeRF Render.json",
    "blender": (3, 0, 0),
    "category": "Export",
}

import bpy
import json
import math
import mathutils
import numpy as np
from pathlib import Path

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy.props import StringProperty
from turbo_nerf.blender_utility.nerf_render_manager import NeRFRenderManager
from turbo_nerf.renderer.nerf_snapshot_manager import NeRFSnapshotManager

from turbo_nerf.blender_utility.nerf_scene import NeRFScene
from turbo_nerf.constants import (
    MASK_BOX_DIMS_ID,
    MASK_CYLINDER_HEIGHT_ID,
    MASK_CYLINDER_RADIUS_ID,
    MASK_FEATHER_ID,
    MASK_MODE_ID,
    MASK_OPACITY_ID,
    MASK_SPHERE_RADIUS_ID,
    MASK_TYPE_BOX,
    MASK_TYPE_CYLINDER,
    MASK_TYPE_ID,
    MASK_TYPE_SPHERE,
    RENDER_CAM_NEAR_ID,
    RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID,
    RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID,
    RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID,
    RENDER_CAM_SENSOR_HEIGHT_ID,
    RENDER_CAM_SENSOR_WIDTH_ID,
    RENDER_CAM_SPHERICAL_QUAD_CURVATURE_ID,
    RENDER_CAM_TYPE_ID,
    RENDER_CAM_TYPE_PERSPECTIVE,
    RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON,
    RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL,
    NERF_AABB_CENTER_ID,
    NERF_AABB_SIZE_ID,
    NERF_PATH_ID,
    NERF_OPACITY_ID,
)
from turbo_nerf.utility.render_camera_utils import bl2nerf_fl
from turbo_nerf.utility.math import bl2nerf_mat, bl2nerf_pos

def mat_to_list(m: mathutils.Matrix) -> list[float]:
    return [list(r) for r in m]

def get_camera_fovs(blender_camera: bpy.types.Camera):
    scene = bpy.context.scene
    cam_data = blender_camera.data

    # get camera props
    blender_fps = scene.frame_step * scene.render.fps / scene.render.fps_base
    # ngp_time = (scene.frame_end - scene.frame_start) / blender_fps
    render_scale = scene.render.resolution_percentage / 100.0
    ngp_w = scene.render.resolution_x * render_scale
    ngp_h = scene.render.resolution_y * render_scale

    # calculate focal len
    bl_sw = cam_data.sensor_width
    bl_sh = cam_data.sensor_height
    # bl_ax = cam_data.angle_x
    # bl_ay = cam_data.angle_y
    bl_f  = cam_data.lens

    # get blender sensor size in pixels
    px_w: float
    # px_h: float
    
    if cam_data.sensor_fit == 'AUTO':
        bl_asp = 1.0
        ngp_asp = ngp_h / ngp_w

        if ngp_asp > bl_asp:
            px_w = ngp_h / bl_asp
            # px_h = ngp_h
        else:
            px_w = ngp_w
            # px_h = ngp_w * bl_asp

    elif cam_data.sensor_fit == 'HORIZONTAL':
        px_w = ngp_w
        # px_h = ngp_w * bl_sh / bl_sw

    elif cam_data.sensor_fit == 'VERTICAL':
        px_w = ngp_h * bl_sw / bl_sh
        # px_h = ngp_h
    
    
    # focal length in pixels
    px_f = bl_f / bl_sw * px_w

    # ngp fov angles
    ngp_ax = 2.0 * math.atan2(0.5 * ngp_w, px_f)
    ngp_ay = 2.0 * math.atan2(0.5 * ngp_h, px_f)
    
    return (ngp_ax, ngp_ay)


# Serializers

# AABB
def serialize_aabb():
    return {
        "max" : list(NeRFScene.get_aabb_max()),
        "min" : list(NeRFScene.get_aabb_min()),
    }

# Serialize active camera for current frame
def serialize_active_camera(out_dims):
    camera = NeRFRenderManager.get_active_camera()
    m = camera.matrix_world
    
    if camera[RENDER_CAM_TYPE_ID] == RENDER_CAM_TYPE_PERSPECTIVE:
        cam_data = camera.data
        
        # aperture and focus distance
        ngp_aperture = 0
        ngp_focus_target = [0, 0, 0]
        if cam_data.dof.use_dof and cam_data.dof.focus_object != None:
            # No idea if this is correct
            ngp_aperture = cam_data.dof.aperture_fstop
            ngp_focus_target = cam_data.dof.focus_object.matrix_world.translation
            
        cam_json = {
            "type": camera[RENDER_CAM_TYPE_ID],
            "m": bl2nerf_mat(m).tolist(),
            "aperture": ngp_aperture,
            "focus_target": list(ngp_focus_target),
            "near": cam_data.clip_start,
            "far": 1e5,
            "focal_len": bl2nerf_fl(camera, out_dims)
        }
    elif camera[RENDER_CAM_TYPE_ID] == RENDER_CAM_TYPE_SPHERICAL_QUADRILATERAL:
        cam_json = {
            "type": camera[RENDER_CAM_TYPE_ID],
            "sw": camera[RENDER_CAM_SENSOR_WIDTH_ID],
            "sh": camera[RENDER_CAM_SENSOR_HEIGHT_ID],
            "c": camera[RENDER_CAM_SPHERICAL_QUAD_CURVATURE_ID],
            "near": camera[RENDER_CAM_NEAR_ID],
            "m": bl2nerf_mat(m).tolist(),
        }
    elif camera[RENDER_CAM_TYPE_ID] == RENDER_CAM_TYPE_QUADRILATERAL_HEXAHEDRON:
        cam_json = {
            "type": camera[RENDER_CAM_TYPE_ID],
            "fs": list(camera[RENDER_CAM_QUAD_HEX_FRONT_SENSOR_SIZE_ID]),
            "bs": list(camera[RENDER_CAM_QUAD_HEX_BACK_SENSOR_SIZE_ID]),
            "sl": camera[RENDER_CAM_QUAD_HEX_SENSOR_LENGTH_ID],
            "m": bl2nerf_mat(m).tolist(),
            "near": camera[RENDER_CAM_NEAR_ID],
        }
    
    return cam_json

# snapshot = None means global masks
def serialize_masks(snapshot=None):
    masks = [m for m in NeRFRenderManager.get_all_masks() if m.parent == snapshot]
    mask_json = []
    for mask in masks:
        specific_props = {}
        if mask[MASK_TYPE_ID] == MASK_TYPE_BOX:
            specific_props = {
                "dims": list(mask[MASK_BOX_DIMS_ID]),
            }
        elif mask[MASK_TYPE_ID] == MASK_TYPE_CYLINDER:
            specific_props = {
                "radius": mask[MASK_CYLINDER_RADIUS_ID],
                "height": mask[MASK_CYLINDER_HEIGHT_ID],
            }
        elif mask[MASK_TYPE_ID] == MASK_TYPE_SPHERE:
            specific_props = {
                "radius": mask[MASK_SPHERE_RADIUS_ID],
            }

        mask_json.append({
            "shape": mask[MASK_TYPE_ID],
            "mode": mask[MASK_MODE_ID],
            "feather": mask[MASK_FEATHER_ID],
            "opacity": mask[MASK_OPACITY_ID],
            "transform": bl2nerf_mat(mask.matrix_local).tolist(),
            **specific_props
        })
    
    return mask_json

def serialize_nerfs():
    nerfs = NeRFSnapshotManager.get_all_snapshots()
    nerfs_json = []
    bl_rot = np.array([
        [0, 0, 1, 0],
        [-1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 1],
    ])
    for nerf in nerfs:
        aabb_center = nerf[NERF_AABB_CENTER_ID]
        aabb_size = nerf[NERF_AABB_SIZE_ID]
        nerfs_json.append({
            "path": nerf[NERF_PATH_ID],
            "opacity": nerf[NERF_OPACITY_ID],
            "transform": np.matmul(bl2nerf_mat(nerf.matrix_world, origin=[0.0, 0.0, 0.0], scale=1.0), bl_rot).tolist(),
            "aabb": {
                "min": bl2nerf_pos(
                    np.array([
                        aabb_center[0] - aabb_size[0] / 2,
                        aabb_center[1] - aabb_size[1] / 2,
                        aabb_center[2] - aabb_size[2] / 2,
                    ]),
                ).tolist(),
                "max": bl2nerf_pos(
                    np.array([
                        aabb_center[0] + aabb_size[0] / 2,
                        aabb_center[1] + aabb_size[1] / 2,
                        aabb_center[2] + aabb_size[2] / 2,
                    ])
                ).tolist(),
            },
            "modifiers": {
                "masks": serialize_masks(nerf),
            }
        })
    
    return nerfs_json

class BlenderNeRFExportRenderJSON(bpy.types.Operator):

    """Export main camera as NeRF render.json"""
    bl_idname = "turbo_nerf.export_render_json"
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
        

        # TODO: maybe add an eyedropper for this in the blender UI somehow
        # aka don't hardcode the name of this ref object
        offset_matrix = mathutils.Matrix.Identity(4)
        global_transform = NeRFScene.global_transform()
        # if global_transform != None:
        #     offset_matrix = global_transform.matrix_world.inverted()

        render_scale = scene.render.resolution_percentage / 100.0
        ngp_w = scene.render.resolution_x * render_scale
        ngp_h = scene.render.resolution_y * render_scale

        # Walk through all frames, create a camera dict for each frame
        frames = []
        i = 0
        for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
            scene.frame_set(frame)
            
            cam_data = serialize_active_camera((ngp_w, ngp_h))
            mask_data = serialize_masks()
            nerf_data = serialize_nerfs()
            
            # create dict for this frame
            frame_dict = {
                "file_path": f"{i:05d}.png",
                "camera": cam_data,
                "modifiers": {
                    "masks": mask_data,
                },
                "nerfs": nerf_data,
                "n_steps": NeRFScene.get_training_steps(),
                "time": NeRFScene.get_time(),
            }

            frames.append(frame_dict)
            i = i + 1

            # masks
        
        # Put it all together


        ngp_transforms = {
            "w": ngp_w,
            "h": ngp_h,
            "spp": 16,
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

