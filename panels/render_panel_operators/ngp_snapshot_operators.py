import bpy

import blender_nerf_tools.utility.load_ngp

from blender_nerf_tools.renderer.ngp_testbed_manager import NGPTestbedManager
from blender_nerf_tools.renderer.nerf_snapshot_manager import NeRFSnapshotManager

import pyngp #noqa

bl_info = {
    "name": "Import Instant-NGP Properties",
    "blender": (3, 0, 0),
    "category": "Import",
}
from pathlib import Path

from bpy.props import StringProperty

# Thank you https://blender.stackexchange.com/a/126596/141797

class ImportNGPSnapshotOperator(bpy.types.Operator):

    """Import NeRF Transforms"""
    bl_idname = "blender_nerf_tools.import_ngp_snapshot"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".msgpack"
    filter_glob: StringProperty(default='*.msgpack', options={'HIDDEN'})

    def execute(self, context):
        input_path = Path(self.filepath)
        print(f"Importing instant-ngp snapshot from: {input_path}")

        NGPTestbedManager.load_snapshot(input_path)
        NeRFSnapshotManager.add_snapshot(input_path)

        # Open JSON file and interpret
        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}
