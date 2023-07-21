import bpy
from pathlib import Path
from turbo_nerf.blender_utility.nerf_obj_utils import create_obj_for_nerf

from turbo_nerf.utility.nerf_manager import NeRFManager

class ImportNetworkSnapshotOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.import_network_snapshot"
    bl_label = "Import Snapshot"
    bl_options = {'REGISTER', 'UNDO'}

    # You can add properties here if needed, e.g.
    # file_path: bpy.props.StringProperty(name="File Path", default="//network_snapshot.json")
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".turbo"
    filter_glob: bpy.props.StringProperty(default='*.turbo', options={'HIDDEN'})

    def execute(self, context):
        print(f"Importing snapshot from {self.filepath}")

        nerf = NeRFManager.load_nerf(Path(self.filepath))
        create_obj_for_nerf(context, nerf)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
