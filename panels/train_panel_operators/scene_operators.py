import bpy
import numpy as np

from turbo_nerf.blender_utility.nerf_scene import NeRFScene

class BlenderNeRFAutoAlignSceneOperator(bpy.types.Operator):
    bl_idname = "nerf.auto_align_scene"
    bl_label = "Auto Align Scene"
    bl_description = "Aligns the scene to the camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        return {'FINISHED'}
    

class BlenderNeRFFitSceneInBoundingBoxOperator(bpy.types.Operator):
    bl_idname = "nerf.fit_scene_in_bounding_box"
    bl_label = "Fit Scene in Bounding Box"
    bl_description = "Fits the scene in the bounding box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cameras = NeRFScene.get_all_cameras()
        
        if len(cameras) == 0:
            self.report({'ERROR'}, "No camera found in the scene")
            return {'CANCELLED'}
        
        aabb_size = np.array(NeRFScene.get_aabb_size())

        cps = np.array([c.matrix_world.to_translation() for c in cameras])

        cminx, cminy, cminz = np.min(cps[:,0]), np.min(cps[:,1]), np.min(cps[:,2])
        cmaxx, cmaxy, cmaxz = np.max(cps[:,0]), np.max(cps[:,1]), np.max(cps[:,2])

        c_offset = 0.5 * np.array([cminx + cmaxx, cminy + cmaxy, cminz + cmaxz])
        c_size = np.array([cmaxx - cminx, cmaxy - cminy, cmaxz - cminz])

        scale = np.min(aabb_size / c_size)

        glob_tf = NeRFScene.global_transform()
        glob_tf.matrix_world[0][3] -= c_offset[0]
        glob_tf.matrix_world[1][3] -= c_offset[1]
        glob_tf.matrix_world[2][3] -= c_offset[2]

        glob_tf.scale *= scale
        

        return {'FINISHED'}