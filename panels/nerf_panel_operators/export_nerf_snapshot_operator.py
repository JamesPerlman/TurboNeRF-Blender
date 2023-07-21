import bpy
from pathlib import Path

from turbo_nerf.blender_utility.obj_type_utility import get_active_nerf_obj
from turbo_nerf.utility.nerf_manager import NeRFManager

class ExportNetworkSnapshotOperator(bpy.types.Operator):
    bl_idname = "turbo_nerf.export_network_snapshot"
    bl_label = "Export Snapshot"
    bl_options = {'REGISTER', 'UNDO'}

    # You can add properties here if needed, e.g.
    # file_path: bpy.props.StringProperty(name="File Path", default="//network_snapshot.json")
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".turbo"
    filter_glob: bpy.props.StringProperty(default='*.turbo', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        nerf_obj = get_active_nerf_obj(context)

        if nerf_obj is None:
            return False
        
        nerf = NeRFManager.get_nerf_for_obj(nerf_obj)

        return nerf.training_step > 0

    def execute(self, context):
        nerf_obj = get_active_nerf_obj(context)
        
        # enforce that file_path ends with .turbo
        snapshot_path = Path(self.filepath)
        if snapshot_path.suffix != ".turbo":
            snapshot_path = snapshot_path.with_suffix(".turbo")
        
        NeRFManager.save_nerf(nerf_obj, snapshot_path)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        
        active_nerf_obj = get_active_nerf_obj(context)
        nerf = NeRFManager.get_nerf_for_obj(active_nerf_obj)
    
        self.filepath = f"snapshot-step-{nerf.training_step}.turbo"
        
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}
